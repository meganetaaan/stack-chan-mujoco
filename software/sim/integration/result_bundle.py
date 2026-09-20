"""Common evidence envelope for MuJoCo, circuit, structural and SIL analyses.

Models/assumptions and observations are separate; pass/fail comes from gates
fixed before execution. Files are hashed relative to their respective roots.
"""
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import platform
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[3]
DOMAINS={'mujoco','circuits','structural','sil','actuator'}
STATUSES={'assumed','datasheet','measured','derived'}


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate(report):
    if report.get('schema_version')!=1 or report.get('domain') not in DOMAINS:
        raise ValueError('unsupported schema/domain')
    for name in ['commands','inputs','parameters','gates','artifacts']:
        if not isinstance(report.get(name),list):raise ValueError(name+' must be an array')
    for p in report['parameters']:
        if p.get('status') not in STATUSES or not all(k in p for k in ['name','value','unit','source']):
            raise ValueError('parameter needs value, unit and evidence status/source')
    if not report['gates'] or any(type(g.get('passed')) is not bool or not g.get('criterion') for g in report['gates']):
        raise ValueError('explicit gates required')
    if type(report.get('passed')) is not bool or report['passed']!=all(g['passed'] for g in report['gates']):
        raise ValueError('overall pass disagrees with gates')
    for record in report['inputs']+report['artifacts']:
        path=Path(record['path'])
        if path.is_absolute() or '..' in path.parts or len(record.get('sha256',''))!=64:
            raise ValueError('relative path and SHA256 required')
    json.dumps(report,allow_nan=False)
    return report


def write_bundle(out,domain,commands,inputs,parameters,gates,limitations):
    out=Path(out)
    versions={}
    for name in ['mujoco','numpy','scipy','gymnasium']:
        try:versions[name]=importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:pass
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    # The commit alone is insufficient for runs on an uncommitted worktree.
    source_paths=sorted(p for p in (ROOT/'software').rglob('*.py') if '__pycache__' not in str(p))
    report={'schema_version':1,'domain':domain,'commit':commit,
            'runtime':{'python':sys.version,'platform':platform.platform(),'packages':versions},
            'commands':commands,'inputs':[{'path':str(Path(p).relative_to(ROOT)),'sha256':sha(p)} for p in sorted(set([Path(p) for p in inputs]+source_paths))],
            'parameters':parameters,'gates':gates,'passed':all(g['passed'] for g in gates),
            'artifacts':[{'path':str(p.relative_to(out)),'sha256':sha(p)} for p in sorted(out.rglob('*')) if p.is_file() and p.name!='result.json'],
            'limitations':limitations}
    validate(report)
    (out/'result.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    return report
