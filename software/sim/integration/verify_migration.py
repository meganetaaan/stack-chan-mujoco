"""Verify every preserved model, policy, CAD source and historical evidence byte."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def verify():
    manifest=json.loads((ROOT/'docs/prototype/migration_manifest.json').read_text())
    failures=[]
    for original, item in manifest['files'].items():
        path=ROOT/item['path']
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=item['sha256']:
            failures.append(original)
    return {'baseline_commit':manifest['baseline_commit'],'files':len(manifest['files']),
            'failures':failures,'passed':not failures}


if __name__=='__main__':
    result=verify();print(json.dumps(result,indent=2))
    raise SystemExit(0 if result['passed'] else 1)
