#!/usr/bin/env python3
"""Run a predeclared development seed list without replacing failures."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import subprocess
import sys


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--design',type=Path,required=True)
    parser.add_argument('--reference',type=Path,required=True)
    parser.add_argument('--seeds',type=int,nargs='+',required=True)
    parser.add_argument('--workers',type=int,default=4)
    parser.add_argument('--out',type=Path,required=True)
    a=parser.parse_args()
    protocol=Path('configs/maneuver/acceptance_v1.json')
    p=json.loads(protocol.read_text());reserved=set(p['fixed_seeds']+p['randomized_seeds'])
    if len(set(a.seeds))!=len(a.seeds) or reserved.intersection(a.seeds):parser.error('unique development seeds required')
    if a.out.exists() or not 1<=a.workers<=12:parser.error('new output and 1..12 workers required')
    duration=sum(s['duration_s'] for s in p['segments'])
    asset_manifest=a.design/'FROZEN_FILES.json'
    asset_files=json.loads(asset_manifest.read_text())
    if any(sha(a.design/name)!=digest for name,digest in asset_files.items()):parser.error('frozen asset mismatch')
    sources=[asset_manifest,*[a.design/name for name in asset_files],Path(__file__),Path('probe_yaw_dynamics_candidate.py'),protocol,a.reference,
             a.design/'models/scene.xml',a.design/'robot.json',
             *sorted(Path('stackchan_rl').glob('*.py')),Path(p['physics_baseline'])]
    frozen={str(path):sha(path) for path in sources}
    command=[sys.executable,'probe_yaw_dynamics_candidate.py','--design',str(a.design),
             '--reference',str(a.reference),'--protocol',str(protocol),'--duration',str(duration),
             '--static-torque-scale','1','--yaw-kp','6','--yaw-kd','.13','--randomize']
    a.out.mkdir(parents=True)
    manifest={'scope':__doc__,'formal_acceptance':False,'seeds':a.seeds,'workers':a.workers,
              'command_prefix':command,'source_sha256':frozen,'failure_replacements_allowed':False,
              'runtime':{'python':sys.version,'packages':{name:version(name) for name in ['mujoco','numpy','scipy','gymnasium']}}}
    (a.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')

    def run(seed):
        if any(sha(path)!=digest for path,digest in frozen.items()):
            return {'seed':seed,'error':'source changed before trial','development_trial_pass':False}
        output=a.out/str(seed)
        with (a.out/(str(seed)+'.log')).open('w') as log:
            result=subprocess.run(command+['--seed',str(seed),'--out',str(output)],stdout=log,stderr=subprocess.STDOUT)
        report=output/'report.json'
        if result.returncode or not report.exists():
            return {'seed':seed,'error':'trial process failed','returncode':result.returncode,'development_trial_pass':False}
        r=json.loads(report.read_text())
        return {k:r[k] for k in ['seed','time_s','failure','complete_schedule','valid_landings',
                                'landing_requirements_pass','development_trial_pass']}|{
                    'motion_pass':r['motion_scoring']['motion_pass'],'report_sha256':sha(report)}

    rows=[]
    with ThreadPoolExecutor(max_workers=a.workers) as pool:
        for future in as_completed([pool.submit(run,seed) for seed in a.seeds]):
            row=future.result();rows.append(row)
            with (a.out/'progress.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
            print(json.dumps(row),flush=True)
    changed=[path for path,digest in frozen.items() if sha(path)!=digest]
    summary={'formal_acceptance':False,'requested':len(a.seeds),'completed':len(rows),
             'successes':sum(r['development_trial_pass'] for r in rows) if not changed else None,
             'sources_changed':changed,'trials':sorted(rows,key=lambda r:r['seed'])}
    (a.out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({'completed':len(rows),'successes':summary['successes'],'sources_changed':changed}),flush=True)
    if changed:raise SystemExit(1)


if __name__=='__main__':main()
