"""16 einzelne Quellmutanten ausschliesslich in temporaeren Kopien pruefen."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

from firmwarepruefung import ROOT, clean_env, hashes, measurement_hashes

# ID, Quelle, exakt einmal zu ersetzender Text, Ersatz, gezielter Regressionstest.
MUTANTS = (
 ('kern_threshold','kern.py','anteil >= 0.6','anteil > 0.6','PythonRegressionen.test_kern_schwelle_inklusive'),
 ('kern_horizon','kern.py','MAX_BLICK = 600','MAX_BLICK = 599','PythonRegressionen.test_kern_blick_600'),
 ('kern_gap','kern.py','self.zustand if abstand == 1 else None','self.zustand if abstand <= 2 else None','PythonRegressionen.test_kern_luecke_keine_transition'),
 ('kern_dwell','kern.py','if vorher is not None and jetzt != vorher:','if vorher is not None:','PythonRegressionen.test_kern_startwert_bleiben'),
 ('vok_threshold','vokabular.py','modell.kritisch_binnen(wort, horizont) >= schwelle','modell.kritisch_binnen(wort, horizont) > schwelle','PythonRegressionen.test_vokabular_schwelle_inklusive'),
 ('vok_horizon','vokabular.py','naechster - t <= horizont','naechster - t < horizont','PythonRegressionen.test_vokabular_horizont_inklusive'),
 ('vok_initial_phase','vokabular.py','return [p for p in laeufe([kritisch(w) for w in woerter], zusammen) if p[0] > 0]', 'return [p for p in laeufe([kritisch(w) for w in woerter], zusammen) if p[0] >= 0]','PythonRegressionen.test_vokabular_anfangsphase'),
 ('vok_dwell','vokabular.py','if self.startwert and jetzt != vorher:','if self.startwert:','PythonRegressionen.test_vokabular_startwert_bleiben'),
 ('restart_checksum','neustart.py','if not hmac.compare_digest(umschlag["sha256"], hashlib.sha256(kodiert(d)).hexdigest()):','if False:','PythonRegressionen.test_neustart_checksum'),
 ('restart_source','neustart.py','if d["quelle"] != quelle:','if False:','PythonRegressionen.test_neustart_quelle'),
 ('restart_total','neustart.py','if sum(sum(row.values()) for row in g.gewichte.values()) > d["takt"]:','if False:','PythonRegressionen.test_neustart_gesamtmasse'),
 ('restart_bool','neustart.py','type(d["takt"]) is not int','not isinstance(d["takt"], int)','PythonRegressionen.test_neustart_bool_takt'),
 ('cpp_threshold','esp32/Lernknoten/Knoten.h','ausfallBinnen(jetzt) >= 0.6','ausfallBinnen(jetzt) > 0.6','FirmwareRegressionen.test_cpp_schwelle_inklusive'),
 ('cpp_horizon','esp32/Lernknoten/Knoten.h','maxBlick = 600','maxBlick = 599','FirmwareRegressionen.test_cpp_blick_600'),
 ('cpp_dwell','esp32/Lernknoten/Knoten.h','regel == Regel::STARTWERT && vorher != UNBEKANNT && jetzt != vorher','regel == Regel::STARTWERT && vorher != UNBEKANNT','FirmwareRegressionen.test_cpp_startwert_bleiben'),
 ('cpp_total','esp32/Lernknoten/Knoten.h','if (summe > takt) return false;','if (summe > takt + 1.0) return false;','FirmwareRegressionen.test_cpp_gesamtmasse'),
)

# The detailed unittest trace remains only in memory. Published result contains
# test IDs and neutral exception classes, never absolute paths or local identities.
RUNNER = r'''
import io,json,sys,unittest
suite=unittest.defaultTestLoader.loadTestsFromName(sys.argv[1])
r=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
def kind(trace):
    last=trace.rstrip().splitlines()[-1] if trace.strip() else ''
    name=last.split(':',1)[0]
    return name if name.isidentifier() else 'TEST_FAILURE'
print(json.dumps(dict(tests=r.testsRun,failures=[dict(test=t.id(),kind=kind(s)) for t,s in r.failures],
 errors=[dict(test=t.id(),kind=kind(s)) for t,s in r.errors],skipped=len(r.skipped))))
raise SystemExit(0 if r.wasSuccessful() else (2 if r.errors else 1))
'''


def test_run(root, target):
    try:
        p=subprocess.run([sys.executable,'-B','-c',RUNNER,target],cwd=root,env=clean_env(),
                         capture_output=True,text=True,timeout=300)
    except subprocess.TimeoutExpired:
        return dict(classification='TIMEOUT',exit_code=None)
    try:
        data=json.loads(p.stdout.strip().splitlines()[-1])
    except (ValueError,IndexError):
        return dict(classification='RUNNER_ERROR',exit_code=p.returncode)
    data['exit_code']=p.returncode
    data['classification']='ERROR' if data['errors'] else ('ASSERTION_FAILURE' if data['failures'] else 'PASS')
    return data


def copy_sources(target):
    # Explicit source whitelist. No recordings, .git, AGENTS, reports or archives.
    for p in ROOT.glob('*.py'):
        shutil.copyfile(p,target/p.name)
    shutil.copytree(ROOT/'esp32',target/'esp32',ignore=shutil.ignore_patterns('.pio','__pycache__','*.bin','*.elf','*.csv','*.json'))
    # Explicitly synthetic replacement of the tiny loopback fixture expected by
    # the unchanged existing test. No recordings are opened or copied.
    (target/'beispiele').mkdir()
    rows=['takt,start_ms,dauer_ms,ergebnis']
    rows += [f'{i},{i*100},1,' + ('VERBUNDEN' if i <= 6 else 'ABGELEHNT') for i in range(1,13)]
    (target/'beispiele/loopback-roh.csv').write_text('\n'.join(rows)+'\n')


def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument('--output',required=True,type=Path)
    args=a.parse_args()
    before=hashes()
    result=dict(schema='oscan-mutations-v1',source_hashes=before,measurement_hashes=measurement_hashes(),
                fixture='Synthetischer Ersatz: 6 VERBUNDEN, 6 ABGELEHNT; keine Aufnahme gelesen/kopiert',
                mutation_catalog_sha256=hashlib.sha256(json.dumps(MUTANTS).encode()).hexdigest(),mutants=[])
    with tempfile.TemporaryDirectory(prefix='oscan-original-') as d:
        root=Path(d);copy_sources(root)
        if hashes(root)!=before:raise RuntimeError('COPY_HASH_MISMATCH')
        result['baseline_existing']=test_run(root,'test_labor')
        result['baseline_new']=test_run(root,'test_firmwarepruefung')
    if any(result[k]['classification']!='PASS' for k in ('baseline_existing','baseline_new')):
        args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
        raise SystemExit('BASELINE_NOT_GREEN')
    for name,file,old,new,target in MUTANTS:
        with tempfile.TemporaryDirectory(prefix='oscan-mutant-') as d:
            root=Path(d)
            copy_sources(root)
            if hashes(root)!=before:raise RuntimeError('COPY_HASH_MISMATCH')
            p=root/file
            text=p.read_text()
            if text.count(old)!=1:
                raise RuntimeError('MUTATION_LOCATION:'+name)
            p.write_text(text.replace(old,new,1))
            row=dict(id=name,file=file,original=old,replacement=new,regression='test_firmwarepruefung.'+target)
            row['existing']=test_run(root,'test_labor')
            row['targeted']=test_run(root,row['regression'])
            row['existing_survivor']=row['existing']['classification']=='PASS'
            row['targeted_killed']=row['targeted']['classification']=='ASSERTION_FAILURE'
            result['mutants'].append(row)
            print(json.dumps(dict(progress='mutation',id=name,existing=row['existing']['classification'],
                                  targeted=row['targeted']['classification'])),flush=True)
            # Incremental neutral result makes long runs auditable without raw logs.
            args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    result['source_hashes_after']=hashes()
    result['sources_unchanged']=before==result['source_hashes_after']
    result['measurement_unchanged']=result['measurement_hashes']==measurement_hashes()
    result['totals']=dict(mutants=len(result['mutants']),
        existing_survivors=sum(x['existing_survivor'] for x in result['mutants']),
        existing_assertion_failures=sum(x['existing']['classification']=='ASSERTION_FAILURE' for x in result['mutants']),
        existing_errors=sum(x['existing']['classification']=='ERROR' for x in result['mutants']),
        targeted_killed=sum(x['targeted_killed'] for x in result['mutants']))
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result['totals'],sort_keys=True))
    if not result['sources_unchanged'] or not result['measurement_unchanged'] or not all(x['targeted_killed'] for x in result['mutants']):raise SystemExit(1)


if __name__=='__main__':main()
