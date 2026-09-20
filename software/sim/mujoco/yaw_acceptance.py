"""Frozen-candidate admission for the predeclared maneuver acceptance seeds.

This module does not run trials. A snapshot alone is never acceptance evidence.
"""
import gzip
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import shutil
import sys

PROTOCOL=Path('configs/maneuver/acceptance_v1.json')
PROTOCOL_SHA='3fba1d1c37b92dc24f69c6ac2c300916b98df6b2c9cf1ef5dffcd25acbc1e347'
CONTROLS={'duration':205.,'static_torque_scale':1.,'yaw_kp':6.,'yaw_kd':.13,
          'ankle_kd':None,'attitude_gain':0.,'attitude_rate_gain':0.,
          'attitude_axes':'both','imu_delay_s':.02,'physics_dt_s':.001,'policy':None}


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def runtime():
    return {'python':sys.version,'packages':{name:version(name) for name in ['mujoco','numpy','scipy','gymnasium']}}


def dependencies(design,reference,protocol):
    assets=json.loads((design/'FROZEN_FILES.json').read_text())
    return [Path(__file__),Path('probe_yaw_dynamics_candidate.py'),Path('run_yaw_acceptance.py'),PROTOCOL,reference,
            design/'FROZEN_FILES.json',*[design/name for name in assets],
            *sorted(Path('stackchan_rl').glob('*.py')),Path(protocol['physics_baseline'])]


def create_snapshot(design,reference,out):
    design,reference,out=map(Path,(design,reference,out))
    if out.exists():raise ValueError('new snapshot directory required')
    if sha(PROTOCOL)!=PROTOCOL_SHA:raise ValueError('predeclared protocol changed')
    protocol=json.loads(PROTOCOL.read_text())
    rows=json.loads(gzip.decompress(reference.read_bytes()))
    if len(rows)!=10251 or any(abs(r['time_s']-i*.02)>1e-9 for i,r in enumerate(rows)):
        raise ValueError('complete 205 second reference required')
    assets=json.loads((design/'FROZEN_FILES.json').read_text())
    if any(sha(design/name)!=digest for name,digest in assets.items()):raise ValueError('frozen asset mismatch')
    out.mkdir(parents=True)
    target=out/'reference.json.gz';shutil.copy2(reference,target)
    sources=dependencies(design,target,protocol)
    result={'schema':'yaw-maneuver-acceptance-snapshot-v1','protocol_sha256':PROTOCOL_SHA,
            'design':str(design),'reference':str(target),'controls':CONTROLS,
            'fixed_seeds':protocol['fixed_seeds'],'randomized_seeds':protocol['randomized_seeds'],
            'required_successes':protocol['required_successes'],'runtime':runtime(),
            'source_sha256':{str(p):sha(p) for p in sources},'trial_results':None}
    (out/'snapshot.json').write_text(json.dumps(result,indent=2)+'\n')
    return out/'snapshot.json'


def validate_trial(args):
    allowed=set(CONTROLS)|{'acceptance_manifest','protocol','design','reference','seed','randomize','out','record_contact_trace'}
    if set(vars(args))-allowed:raise ValueError('unreviewed trial option')
    path=Path(args.acceptance_manifest);snapshot=json.loads(path.read_text())
    if snapshot['schema']!='yaw-maneuver-acceptance-snapshot-v1':raise ValueError('unknown snapshot schema')
    if sha(PROTOCOL)!=PROTOCOL_SHA or snapshot['protocol_sha256']!=PROTOCOL_SHA:
        raise ValueError('predeclared protocol changed')
    protocol=json.loads(PROTOCOL.read_text())
    for key in ['fixed_seeds','randomized_seeds','required_successes']:
        if snapshot[key]!=protocol[key]:raise ValueError('acceptance schedule changed')
    group='randomized_seeds' if args.randomize else 'fixed_seeds'
    if args.seed not in snapshot[group]:raise ValueError('seed does not belong to the acceptance group')
    if snapshot['controls']!=CONTROLS:raise ValueError('unsupported candidate controls')
    for key,value in CONTROLS.items():
        if getattr(args,key)!=value:raise ValueError('control override: '+key)
    if Path(args.protocol).resolve()!=PROTOCOL.resolve():raise ValueError('different protocol path')
    if Path(args.design).resolve()!=Path(snapshot['design']).resolve():raise ValueError('different candidate model')
    if Path(args.reference).resolve()!=Path(snapshot['reference']).resolve():raise ValueError('different reference')
    if snapshot['runtime']!=runtime():raise ValueError('runtime changed')
    required={str(p) for p in dependencies(Path(snapshot['design']),Path(snapshot['reference']),protocol)}
    if required!=set(snapshot['source_sha256']):raise ValueError('incomplete dependency snapshot')
    for name,digest in snapshot['source_sha256'].items():
        if sha(name)!=digest:raise ValueError('frozen dependency changed: '+name)
    return {'manifest_path':str(path),'manifest_sha256':sha(path),'group':'randomized' if args.randomize else 'fixed'}


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--design',type=Path,required=True)
    parser.add_argument('--reference',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    a=parser.parse_args()
    print(create_snapshot(a.design,a.reference,a.out))
