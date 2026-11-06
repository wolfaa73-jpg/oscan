"""Vier lange synthetische Firmware-Lerngeschichten, unveränderter Originalprüfer."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import random
import struct
import subprocess
import sys
import tempfile

import firmwarepruefung as f
from kern import ZUSTAENDE

REGELSEEDS = (('zeit',730101),('kontext',730102),('erbe',730103),('startwert',730104))
BEOBACHTUNGEN = 250000
ABSCHNITT = 62500
LANGER_BLICK = 512
QUELLEN = ('firmwarelanglauf.py','test_firmwarelanglauf.py','FIRMWARE-LANGLAUF-PLAN.md')


def sha(daten):
    return hashlib.sha256(daten).hexdigest()


def eigene_hashes():
    return {n:sha((f.ROOT/n).read_bytes()) for n in QUELLEN}


def klassifiziere(wert):
    if not math.isfinite(wert) or wert < 0:
        return 'ungueltig'
    if wert == 0:
        return 'null'
    return 'subnormal' if wert < sys.float_info.min else 'normal'


def schrittvorgabe(rng, nummer):
    state = ZUSTAENDE[rng.randrange(3)]
    phase = nummer % 64
    forced = phase in (1,2,3)
    if forced:
        state = ('OK','SCHWACH','AUSFALL')[phase-1]
    step = rng.randint(2,7) if nummer % 997 == 0 and not forced else 1
    return state, step, forced


def abschnitt(rule, rng, start, ende, saved=None, total=BEOBACHTUNGEN, tail=LANGER_BLICK):
    o = f.Oracle(rule,saved)
    o.command('NEUER_LAUF')
    o.command('BLICK 1')
    if saved is not None:
        o.command('LADEN')
    diag = dict(first_observation=start, last_observation=ende,
                horizon1=0,horizon600=0,forced_observations=0,weak_exits=0,
                first_subnormal=None,first_zero=None)
    for i in range(start,ende+1):
        if i == total-tail+1:
            o.command('BLICK 600')
        state, step, forced = schrittvorgabe(rng,i)
        if step == 1 and o.node.zustand == 'SCHWACH' and state != 'SCHWACH':
            diag['weak_exits'] += 1
        o.point(o.node.takt+step,state)
        diag['horizon1' if o.node.blick == 1 else 'horizon600'] += 1
        diag['forced_observations'] += int(forced)
        if rule == 'startwert':
            value = o.node.gedaechtnis.erbe['SCHWACH']['AUSFALL']
            kind = klassifiziere(value)
            if kind == 'subnormal' and diag['first_subnormal'] is None:
                diag['first_subnormal'] = i
            if kind == 'null' and diag['first_zero'] is None:
                diag['first_zero'] = i
    o.command('SICHERN')
    return o,diag


def nvs_diagnose(path,node,rule):
    actual = path.read_bytes()
    expected = f.state_bytes(node,rule)
    result = dict(actual_sha256=sha(actual),expected_sha256=sha(expected),
                  bytes_equal=actual==expected,bytes=len(actual))
    n = 18 if rule == 'startwert' else 9
    if len(actual) == len(expected):
        a = struct.unpack_from(f'<{n}d',actual,10)
        e = struct.unpack_from(f'<{n}d',expected,10)
        result['max_matrix_difference'] = max(abs(x-y) for x,y in zip(a,e)) if all(math.isfinite(x) for x in a+e) else None
        if rule == 'startwert':
            # Matrixzeile SCHWACH -> AUSFALL, zweite3x3-Matrix.
            at = 9 + ZUSTAENDE.index('SCHWACH')*3 + ZUSTAENDE.index('AUSFALL')
            result['startwert'] = dict(python_hex=e[at].hex(),firmware_hex=a[at].hex(),
                python_class=klassifiziere(e[at]),firmware_class=klassifiziere(a[at]))
    return result


def bericht(report):
    z=report['totals']
    lines=['# Firmware/Python: Ergänzung durch lange Lerngeschichten','',
        'Ausschließlich künstliche Daten. Vier kontinuierlich fortgelernte Geschichten, keine Million verschiedener Spuren.',
        f'Genau {z["observations"]} Beobachtungen, {z["compared_lines"]} exakt verglichene Protokollzeilen.',
        f'Abweichende Zeilen: {z["mismatch_lines"]}; NVS-Prüffehler: {z["state_errors"]}.',
        f'Blick1: {z["horizon1"]} Beobachtungen; Blick600: {z["horizon600"]}.',
        f'{z["gaps"]} Lücken; {z["saves"]} Sicherungen, {z["loads"]} LADEN und {z["resets"]} NEUER_LAUF.', '',
        '## Zähler pro Regel','',
        '| Regel | Seed | Beobachtungen | Lücken | Ausgänge aus SCHWACH | Ausgabeabweichungen | NVS-Fehler |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for rule,seed in REGELSEEDS:
        rows=[r for r in report['segments'] if r['rule']==rule]
        sums={k:sum(r.get(k,0) for r in rows) for k in ('observations','gaps','weak_exits','mismatch_lines')}
        lines.append(f'| {rule} | {seed} | {sums["observations"]} | {sums["gaps"]} | {sums["weak_exits"]} | '
                     f'{sums["mismatch_lines"]} | {sum(bool(r["state_error"]) for r in rows)} |')
    sw=[r for r in report['segments'] if r['rule']=='startwert']
    first=[r['first_subnormal'] for r in sw if r['first_subnormal'] is not None]
    last=sw[-1]['nvs'].get('startwert',{})
    lines += ['', 'Die Tabelle zählt Paritätsprüfungen, keine Warnleistung; Immer warnen wäre hier kein Oracle für die vier Firmware-Regeln.', '',
        '## Unterlauf und Wiederanlauf','',
        f'Erster beobachteter subnormaler Python-Startwert: Beobachtung {min(first) if first else "nicht erreicht"}.',
        f'Letzter Rest: Python `{last.get("python_hex","nicht lesbar")}`, Firmware `{last.get("firmware_hex","nicht lesbar")}`.',
        f'Klassifikation: Python {last.get("python_class","unbekannt")}, Firmware {last.get("firmware_class","unbekannt")}.',
        'Ein positiver subnormaler Rundungsrest ist nicht automatisch ein Fehler und wird nicht als exakt null ausgegeben.',
        'Nach62500,125000,187500 Beobachtungen wurde gesichert, der eigene Hostprozess beendet und mit',
        'NEUER_LAUF→BLICK1→LADEN aus demselben NVS fortgesetzt. Der absolute Takt lief weiter.',
        'Vier NVS-Stände je Regel wurden geprüft; die zusätzliche Schluss-Sicherung enthält den langen Blickabschnitt.', '',
        '## Integrität und Grenzen','',
        f'Geschützte Quellen unverändert: {report["sources_unchanged"]}; bisherige Prüfer unverändert: {report["old_measurements_unchanged"]}; neue Prüfquellen unverändert: {report["runner_unchanged"]}.',
        f'Vollständig bytegleiche NVS-Stände: {z["nvs_byte_equal"]}/{len(report["segments"])}. Maßgeblich bleibt die vorhandene Matrixregel:',
        'Header/CRC prüfen, endliche Matrixwerte mit absoluter Toleranz2e-12; Protokoll und Warnentscheidungen immer exakt.',
        'Quellhashes, Compilerkennung/-flags und sämtliche Abschnittszähler stehen in [firmware-langlauf.json](firmware-langlauf.json).',
        'Dies ergänzt die vorherigen48-Beobachtungs-Fälle um lange Lerngeschichten. Es ersetzt keinen ESP32-',
        'Flash-/Stromausfall-, Echtzeit- oder Sicherheitsnachweis. Kein Originalcode wurde verändert.', '',
        'Reproduktion im Laborordner:', '',
        '```sh', 'python3 -B -m unittest -v test_firmwarelanglauf',
        'python3 -B firmwarelanglauf.py --ausgabe rechen-ergebnisse/neuer-langlauf', '```','']
    return '\n'.join(lines)


def run(out):
    if out.exists():
        raise ValueError('OUTPUT_EXISTS')
    before, old, own = f.hashes(), f.measurement_hashes(), eigene_hashes()
    compiler = subprocess.run(['c++','--version'],capture_output=True,text=True,check=True).stdout.splitlines()[0]
    report=dict(schema='oscan-firmware-langlauf-v1',source_hashes=before,
                old_measurement_hashes=old,runner_hashes=own,compiler=compiler,
                compiler_arguments=list(f.FLAGS),segments=[])
    with tempfile.TemporaryDirectory(prefix='oscan-long-') as d:
        tmp=Path(d)
        binaries=f.compile_hosts(tmp)
        for rule,seed in REGELSEEDS:
            rng=random.Random(f'OSCAN-FIRMWARE-LANGLAUF-v1:{rule}:{seed}')
            saved=None
            nvs=tmp/(rule+'-state')
            for start in range(1,BEOBACHTUNGEN+1,ABSCHNITT):
                end=start+ABSCHNITT-1
                o,diag=abschnitt(rule,rng,start,end,saved)
                actual=f.run_host(binaries[rule],o.commands,nvs,timeout=120)
                row=dict(rule=rule,seed=seed,**diag,**o.counts,**f.difference(o.expected,actual))
                row['state_error']=f.check_state(nvs,o.saved,rule)
                row['nvs']=nvs_diagnose(nvs,o.saved,rule)
                report['segments'].append(row)
                saved=o.saved
                print(json.dumps(dict(rule=rule,observations_completed=end,
                    mismatch_lines=row['mismatch_lines'],state_error=row['state_error'])),flush=True)
    report['source_hashes_after']=f.hashes()
    report['sources_unchanged']=before==report['source_hashes_after']
    report['old_measurements_unchanged']=old==f.measurement_hashes()
    report['runner_unchanged']=own==eigene_hashes()
    rows=report['segments']
    report['totals']={k:sum(r[k] for r in rows) for k in
        ('observations','gaps','saves','loads','resets','horizon1','horizon600','weak_exits','forced_observations','mismatch_lines')}
    report['totals'].update(compared_lines=sum(r['expected_lines'] for r in rows),
        state_errors=sum(bool(r['state_error']) for r in rows),nvs_byte_equal=sum(r['nvs']['bytes_equal'] for r in rows))
    report['status']='bestanden' if all((report['sources_unchanged'],report['old_measurements_unchanged'],
        report['runner_unchanged'],not report['totals']['mismatch_lines'],not report['totals']['state_errors'])) else 'abweichung'
    out.mkdir(parents=True,exist_ok=False)
    (out/'firmware-langlauf.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    (out/'bericht.md').write_text(bericht(report),encoding='utf-8')
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--ausgabe',required=True,type=Path)
    a=p.parse_args()
    try:
        report=run(a.ausgabe)
    except (ValueError,OSError,RuntimeError,subprocess.SubprocessError) as exc:
        p.exit(2,f'Langlauf abgebrochen ({type(exc).__name__}); keine vollständige Ergebnismeldung.\n')
    print(json.dumps(report['totals'],sort_keys=True))
    if report['status']!='bestanden':
        raise SystemExit(1)


if __name__=='__main__':
    main()
