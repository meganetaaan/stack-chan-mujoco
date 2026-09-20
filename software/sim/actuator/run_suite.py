"""Freeze and run 34 nominal/one-factor CAD leg fixtures plus all 12 joint fixtures."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--workload',required=True,type=Path);p.add_argument('--out',required=True,type=Path)
    a=p.parse_args();out=a.out.resolve();workload=a.workload.resolve()
    if out.exists():p.error('new output required')
    out.mkdir(parents=True)
    cases=[]
    for side in ['left','right']:
        for mode in ['support','transfer','swing']:cases.append({'name':side+'_'+mode+'_nominal','side':side,'mode':mode,'args':[]})
        for factor,option,values,mode in [
            ('voltage','--voltage',[3.7,6.],'swing'),('delay','--delay',[.005,.020],'swing'),
            ('backlash','--backlash',[0.,.017453292519943295],'swing'),
            ('current_tau','--current-tau',[.001,.005],'swing'),
            ('mass','--mass-scale',[.95,1.05],'support'),('friction','--friction-scale',[.5,1.5],'swing')]:
            for value in values:cases.append({'name':f'{side}_{factor}_{value}','side':side,'mode':mode,'args':[option,str(value)]})
    for side in ['left','right']:
        for trajectory in ['forward.npz','backward.npz']:
            cases.append({'name':side+'_'+trajectory[:-4]+'_swing','side':side,'mode':'swing','args':['--trajectory',trajectory]})
    inputs=[p for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in str(p)]+list(workload.glob('*'))
    hashes=lambda:{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
    before=hashes()
    plan={'scope':__doc__,'cases':cases,'sources':before,'workers':4,
          'requirements':json.loads((workload/'requirements.json').read_text()),
          'limitations':['one factor at a time; no statistical hardware reliability estimate','fixtures constrain the torso as documented']}
    (out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    def run(case):
        cmd=[sys.executable,str(HERE/'run_leg.py'),'--workload',str(workload),'--out',str(out/case['name']),
             '--side',case['side'],'--mode',case['mode'],*case['args']]
        with (out/(case['name']+'.log')).open('w') as log:rc=subprocess.run(cmd,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT).returncode
        path=out/case['name']/'report.json'
        report=json.loads(path.read_text()) if path.exists() else {'passed':False,'execution_error':rc}
        row={'case':case['name'],'passed':rc==0 and report['passed'],'report':report,'command':cmd}
        print(json.dumps({'case':case['name'],'passed':row['passed']}),flush=True)
        return row
    with ThreadPoolExecutor(max_workers=4) as pool:rows=list(pool.map(run,cases))
    command=[sys.executable,str(HERE/'run_single_joint.py'),'--workload',str(workload),'--out',str(out/'single_joint')]
    with (out/'single_joint.log').open('w') as log:rc=subprocess.run(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT).returncode
    summary={'scope':__doc__,'passed':all(r['passed'] for r in rows) and rc==0 and before==hashes(),
             'sources_unchanged':before==hashes(),'leg_passed':sum(r['passed'] for r in rows),'leg_total':len(rows),
             'single_joint_passed':rc==0,'rows':rows,'single_joint_command':command}
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({k:v for k,v in summary.items() if k not in ['rows','single_joint_command']},indent=2))
    raise SystemExit(0 if summary['passed'] else 1)


if __name__=='__main__':main()
