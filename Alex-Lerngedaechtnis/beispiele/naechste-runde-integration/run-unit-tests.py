import contextlib,hashlib,io,json,platform,re,time,unittest
from pathlib import Path

def main():
    root=Path.cwd().parent
    log=io.StringIO()
    started=time.monotonic()
    suite=unittest.TestLoader().discover('.')
    with contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
        result=unittest.TextTestRunner(stream=log,verbosity=0).run(suite)
    def classify(trace):
        matches=re.findall(r'^([A-Za-z_][A-Za-z0-9_]*(?:Error|Exception)):',trace,re.MULTILINE)
        return matches[-1] if matches else 'TEST_FAILURE'
    manifest=json.loads((root/'integration-manifest.json').read_text())
    checks=[]
    for name,digest in manifest['base_hashes'].items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest:checks.append(name)
    for files in manifest['overlays'].values():
        for name,digest in files.items():
            if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest:checks.append(name)
    report=dict(base=manifest['base'],python=platform.python_version(),tests=result.testsRun,
     elapsed_seconds=round(time.monotonic()-started,3),
     failures=[dict(test=t.id(),kind=classify(s)) for t,s in result.failures],
     errors=[dict(test=t.id(),kind=classify(s)) for t,s in result.errors],
     skipped=[dict(test=t.id(),reason=str(reason)) for t,reason in result.skipped],
     expected_failures=len(result.expectedFailures),unexpected_successes=len(result.unexpectedSuccesses),
     sources_changed=sorted(set(checks)),overlay_conflicts=manifest['conflicts'],
     success=result.wasSuccessful() and not checks and not manifest['conflicts'])
    (root/'integration-result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False))
    return 0 if report['success'] else 1

if __name__=='__main__':
    raise SystemExit(main())
