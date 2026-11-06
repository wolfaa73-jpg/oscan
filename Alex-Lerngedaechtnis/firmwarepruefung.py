"""Deterministische Firmware-Python-Pruefung; nur synthetische Daten."""
import argparse
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import random
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import zlib

from kern import Knoten, REGELN, ZUSTAENDE
import koerper

ROOT = Path(__file__).resolve().parent
SEEDS = (730001, 730002)
FLAGS = ('-std=c++11', '-Wall', '-Wextra', '-Werror', '-pedantic', '-ffp-contract=off')
PROTECTED = ('kern.py', 'vokabular.py', 'neustart.py', 'esp32/host.cpp',
             'esp32/Lernknoten/Knoten.h', 'esp32/Lernknoten/Lernknoten.ino',
             'esp32/Lernknoten/Koerper.h', 'esp32/Lernknoten/Reize.h')


def hashes(root=ROOT):
    return {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in PROTECTED}


def measurement_hashes():
    names = ('firmwarepruefung.py', 'firmwaremutationen.py', 'test_firmwarepruefung.py', 'FIRMWARE-PRUEFPLAN.md')
    return {n: hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names}


def clean_env():
    env = dict(os.environ)
    env.pop('PYTHONPATH', None)
    env.pop('PYTHONHOME', None)
    env.pop('ALEX_TEST_NVS', None)
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    return env


def compile_hosts(out, root=ROOT):
    result = {}
    for rule in REGELN:
        binary = out / rule
        define = [] if rule == 'zeit' else ['-DALEX_' + rule.upper()]
        p = subprocess.run(['c++', *FLAGS, *define, 'esp32/host.cpp', '-o', str(binary)],
                           cwd=root, env=clean_env(), capture_output=True, timeout=120)
        if p.returncode:
            raise RuntimeError('COMPILER_ERROR:' + rule)
        subprocess.run([str(binary)], input=b'', capture_output=True, timeout=120, check=True)
        result[rule] = binary
    return result


def run_host(binary, commands, nvs, timeout=120):
    p = subprocess.run([str(binary)], input=('\n'.join(commands) + '\n').encode(),
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout,
                       env=dict(clean_env(), ALEX_TEST_NVS=str(nvs)))
    if p.returncode:
        raise RuntimeError('HOST_EXIT:' + str(p.returncode))
    if p.stderr:
        raise RuntimeError('HOST_STDERR')
    return p.stdout.decode('utf-8').splitlines()


class Oracle:
    """Befehlsvertrag separat vom C++-Parser, Lernen ausschliesslich via kern.Knoten."""
    def __init__(self, rule, saved=None):
        self.rule = rule
        self.saved = copy.deepcopy(saved)
        self.reset()
        self.commands = []
        self.expected = ['takt,zustand,sofort,vorwarnung']
        self.counts = dict(observations=0, errors=0, gaps=0, saves=0, loads=0,
                           resets=0, body=0, autosaves=0)

    def reset(self):
        self.node = Knoten(REGELN[self.rule]())
        self.loaded = False
        self.interval = 0

    def emit(self, command, answer):
        self.commands.append(command)
        self.expected.append(answer)

    def command(self, command):
        if command == 'NEUER_LAUF':
            self.reset()
            self.counts['resets'] += 1
            answer = 'BEREIT,' + self.rule.upper()
        elif command.startswith('BLICK '):
            self.node.blick = int(command.split()[1])
            answer = 'BLICK,ok'
        elif command == 'SICHERN':
            if not self.node.takt:
                return self.bad(command)
            self.saved = copy.deepcopy(self.node)
            self.counts['saves'] += 1
            answer = 'GESICHERT'
        elif command == 'LADEN':
            if self.saved is None or self.node.takt:
                self.loaded = False
                return self.bad(command)
            horizon = self.node.blick
            self.node = copy.deepcopy(self.saved)
            self.node.blick = horizon
            self.loaded = True
            self.counts['loads'] += 1
            answer = 'GELADEN'
        elif command.startswith('SICHERN_ALLE '):
            self.interval = int(command.split()[1])
            answer = 'SICHERN_ALLE,ok'
        elif command.startswith('GRENZEN '):
            answer = 'GRENZEN,ok'
        else:
            raise ValueError('ORACLE_COMMAND')
        self.emit(command, answer)

    def bad(self, command):
        self.counts['errors'] += 1
        self.emit(command, 'FEHLER')

    def point(self, tick, state):
        if tick - self.node.takt > 1:
            self.counts['gaps'] += 1
        s = self.node.schritt(tick, state)
        self.counts['observations'] += 1
        self.emit(f'{tick},{state}', f'{tick},{state},{int(s.sofort)},{int(s.vorwarnung)}')

    def body(self, raw):
        temp, heap, gap = raw
        state = koerper.einstufen(temp, heap, gap, koerper.ERKUNDUNG)
        tick = self.node.takt + (2 if self.loaded else 1)
        if self.loaded:
            self.counts['gaps'] += 1
        self.loaded = False
        s = self.node.schritt(tick, state)
        t = '-' if temp is None else str(temp)
        self.counts['observations'] += 1
        self.counts['body'] += 1
        self.emit(f'MESSWERT {t} {heap} {gap}',
                  f'K,{tick},{state},{int(s.sofort)},{int(s.vorwarnung)},{t},{heap},{gap},0')
        if self.interval and tick % self.interval == 0:
            self.saved = copy.deepcopy(self.node)
            self.counts['autosaves'] += 1


def random_case(rule, horizon, seed, saved=None):
    rng = random.Random(f'OSCAN-FIRMWARE-v1:{rule}:{horizon}:{seed}')
    o = Oracle(rule, saved)
    o.command('NEUER_LAUF')
    o.command(f'BLICK {horizon}')
    save_at, load_at = rng.randrange(5, 13), rng.randrange(18, 26)
    bad = ['BLICK 0', 'BLICK 601', 'BLICK 30 1', 'SICHERN_ALLE x',
           '4294967296,OK', '2,OK\x00x', 'X' * 80, '-1,OK', '0,OK', '1,UNBEKANNT']
    for j in range(48):
        if j == load_at:
            o.command('NEUER_LAUF')
            o.command(f'BLICK {horizon}')
            o.command('LADEN')
        if j == 32:
            o.command('NEUER_LAUF')
        if j == 33:
            o.command(f'BLICK {horizon}')
        if j % 8 == 0:
            o.bad(rng.choice(bad))
        if j in (7, 27):
            o.bad(f'{o.node.takt},OK')
        step = rng.randint(2, 9) if j in (7, 27) or rng.random() < .12 else 1
        state = ZUSTAENDE[rng.randrange(3)]
        o.point(o.node.takt + step, state)
        if j == save_at:
            o.command('SICHERN')
    return o


def difference(expected, actual):
    n = max(len(expected), len(actual))
    wrong = [i for i in range(n) if (expected[i] if i < len(expected) else None)
             != (actual[i] if i < len(actual) else None)]
    result = dict(expected_lines=len(expected), actual_lines=len(actual), mismatch_lines=len(wrong))
    if wrong:
        i = wrong[0]
        result['first'] = dict(line=i, expected=expected[i] if i < len(expected) else None,
                               actual=actual[i] if i < len(actual) else None)
    return result


def state_bytes(node, rule):
    g = node.gedaechtnis
    start = rule == 'startwert'
    b = (b'AG02' if start else b'AG01') + bytes((list(REGELN).index(rule)+1,
                                               ZUSTAENDE.index(node.zustand)+1))
    b += struct.pack('<I', node.takt)
    for tab in [g.gewichte] + ([g.erbe] if start else []):
        b += struct.pack('<9d', *(tab[z][f] for z in ZUSTAENDE for f in ZUSTAENDE))
    return b + struct.pack('<I', zlib.crc32(b))


def check_state(path, node, rule):
    b, expected = path.read_bytes(), state_bytes(node, rule)
    if len(b) != len(expected) or b[:10] != expected[:10]:
        return 'STATE_HEADER'
    if struct.unpack('<I', b[-4:])[0] != zlib.crc32(b[:-4]):
        return 'STATE_CRC'
    n = 18 if rule == 'startwert' else 9
    if any(not math.isfinite(a) or abs(a-e) > 2e-12 for a, e in zip(struct.unpack_from(f'<{n}d', b, 10),
                                          struct.unpack_from(f'<{n}d', expected, 10))):
        return 'STATE_MATRIX'
    return None


def parity(out, horizons=range(1, 601), seeds=SEEDS):
    before = hashes()
    compiler = subprocess.run(['c++', '--version'], capture_output=True, text=True, check=True).stdout.splitlines()[0]
    report = dict(schema='oscan-firmware-v1', source_hashes=before, measurement_hashes=measurement_hashes(),
                  plan_sha256=hashlib.sha256((ROOT/'FIRMWARE-PRUEFPLAN.md').read_bytes()).hexdigest(),
                  compiler=compiler, compiler_arguments=list(FLAGS), seeds=list(seeds), cases=[], extras=[])
    with tempfile.TemporaryDirectory(prefix='oscan-fw-') as tmp:
        tmp = Path(tmp)
        binaries = compile_hosts(tmp)
        for rule, binary in binaries.items():
            for seed in seeds:
                # One process per horizon: isolation includes true startup and NVS handling.
                for horizon in horizons:
                    o = random_case(rule, horizon, seed)
                    nvs = tmp / 'state'
                    nvs.unlink(missing_ok=True)
                    actual = run_host(binary, o.commands, nvs)
                    row = dict(rule=rule, horizon=horizon, seed=seed, **o.counts,
                               **difference(o.expected, actual))
                    row['state_error'] = check_state(nvs, o.saved, rule)
                    report['cases'].append(row)
                print(json.dumps(dict(progress='parity', rule=rule, seed=seed)), flush=True)
            for horizon in (1, 2, 30, 600):
                for seed in seeds:
                    rng = random.Random(f'OSCAN-FIRMWARE-BODY-v1:{rule}:{horizon}:{seed}')
                    choices = [(300,100000,1000),(700,8000,350000),(None,90000,1000),
                               (550,100000,1000),(300,30000,1000)]
                    raws = [rng.choice(choices) for _ in range(52)]
                    nvs = tmp/'body-state'
                    nvs.unlink(missing_ok=True)
                    o = Oracle(rule)
                    o.command(koerper.ERKUNDUNG.befehl().decode().strip())
                    o.command(f'BLICK {horizon}')
                    o.command(f'SICHERN_ALLE {rng.choice((3,5,7))}')
                    for raw in raws[:40]: o.body(raw)
                    row = dict(kind='body_before_restart', rule=rule, horizon=horizon, seed=seed,
                               **o.counts, **difference(o.expected, run_host(binary, o.commands, nvs)))
                    row['state_error'] = check_state(nvs, o.saved, rule)
                    report['extras'].append(row)
                    p = Oracle(rule, o.saved)
                    p.command(koerper.ERKUNDUNG.befehl().decode().strip())
                    p.command(f'BLICK {horizon}')
                    p.command('LADEN')
                    for raw in raws[40:]: p.body(raw)
                    report['extras'].append(dict(kind='body_after_restart', rule=rule,
                        horizon=horizon, seed=seed, **p.counts,
                        **difference(p.expected, run_host(binary, p.commands, nvs))))
                    q = Oracle(rule, o.saved)
                    q.command('LADEN')
                    q.command('SICHERN_ALLE 1')
                    q.command('NEUER_LAUF')
                    q.command(koerper.ERKUNDUNG.befehl().decode().strip())
                    q.body(raws[0])
                    report['extras'].append(dict(kind='reset_after_load', rule=rule, horizon=horizon, seed=seed,
                        **q.counts, **difference(q.expected, run_host(binary,q.commands,nvs))))
                    if check_state(nvs, o.saved, rule):
                        report['extras'][-1]['state_error'] = 'RESET_CHANGED_NVS'
        for old in ('zeit', 'kontext', 'erbe'):
            k = Knoten(REGELN[old]())
            for t, z in enumerate(('OK','SCHWACH','AUSFALL','OK'), 1): k.schritt(t,z)
            nvs = tmp/'ag01'
            nvs.write_bytes(state_bytes(k, old))
            commands = ['LADEN','1,SCHWACH']
            expect = ['takt,zustand,sofort,vorwarnung','FEHLER','1,SCHWACH,0,1']
            report['extras'].append(dict(kind='AG01_into_startwert', old_rule=old, observations=1,
                **difference(expect, run_host(binaries['startwert'], commands, nvs))))
        for rule, binary in binaries.items():
            o = Oracle(rule)
            o.point(2**32-1,'SCHWACH')
            o.bad('4294967296,OK')
            o.bad('4294967295,AUSFALL')
            report['extras'].append(dict(kind='uint32_limit', rule=rule, **o.counts,
                **difference(o.expected, run_host(binary,o.commands,tmp/'unused'))))
    report['source_hashes_after'] = hashes()
    report['sources_unchanged'] = before == report['source_hashes_after']
    report['measurement_unchanged'] = report['measurement_hashes'] == measurement_hashes()
    rows = report['cases'] + report['extras']
    report['totals'] = dict(cases=len(report['cases']), extra_cases=len(report['extras']),
        observations=sum(r.get('observations',0) for r in rows),
        compared_lines=sum(r['expected_lines'] for r in rows),
        mismatch_lines=sum(r['mismatch_lines'] for r in rows),
        state_errors=sum(bool(r.get('state_error')) for r in rows))
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--smoke',action='store_true',help='Nur Horizonte 1,30,600 und erster Seed')
    a=p.parse_args()
    report=parity(a.output, (1,30,600) if a.smoke else range(1,601), SEEDS[:1] if a.smoke else SEEDS)
    print(json.dumps(report['totals'],sort_keys=True))
    if not report['sources_unchanged'] or not report['measurement_unchanged'] or report['totals']['mismatch_lines'] or report['totals']['state_errors']:
        raise SystemExit(1)


if __name__=='__main__': main()
