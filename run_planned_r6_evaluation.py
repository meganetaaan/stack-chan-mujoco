#!/usr/bin/env python3
"""Run both complete acceptance batches from the predeclared seed plan."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parent


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--checkpoint',type=Path,required=True)
    p.add_argument('--seed-plan',type=Path,default=ROOT/'configs/r6/next_evaluation_seeds.json')
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--workers-per-batch',type=int,default=6)
    a=p.parse_args()
    if a.out.exists():p.error('use a new output directory')
    if not 1<=a.workers_per_batch<=6:p.error('workers per batch must be 1..6')
    plan=json.loads(a.seed_plan.read_text());config=json.loads((a.checkpoint/'config.json').read_text())
    if config['schema']!='r6-residual-heading-v2' or config['training']['seed']!=plan['heading_training_seed']:
        p.error('checkpoint does not match the predeclared heading training seed')
    sets=[plan[k] for k in ('fixed_seeds','randomized_seeds')]
    for seeds in sets:
        if len(seeds)!=20 or any(type(x)!=int for x in seeds) or seeds!=list(range(seeds[0],seeds[0]+20)):
            p.error('each batch requires exactly 20 predeclared consecutive integer seeds')
    if set(sets[0])&set(sets[1]):p.error('batch seeds overlap')
    result=json.loads((a.checkpoint/'training_result.json').read_text())
    if not result['trained'] or result['policy_sha256']!=sha(a.checkpoint/'policy.zip'):
        p.error('trained policy missing or hash mismatch')
    a.out.mkdir(parents=True)
    manifest={'scope':'both predeclared R6 simulation acceptance batches',
        'seed_plan':plan,'seed_plan_sha256':sha(a.seed_plan),
        'policy_sha256':result['policy_sha256'],'training_config_sha256':sha(a.checkpoint/'config.json'),
        'runner_sha256':sha(__file__),'evaluator_sha256':sha(ROOT/'evaluate_residual.py'),
        'complete':False,'simulation_criteria_met':False,'hardware_tested':False,'commands':{},'batches':{}}
    processes=[];logs=[]
    try:
        for domain,seeds in zip(('fixed','randomized'),sets):
            cmd=[sys.executable,str(ROOT/'evaluate_residual.py'),'--checkpoint',str(a.checkpoint.resolve()),
                '--out',str((a.out/domain).resolve()),'--domain',domain,'--seed',str(seeds[0]),
                '--episodes','20','--purpose','acceptance','--workers',str(a.workers_per_batch)]
            manifest['commands'][domain]=cmd
        (a.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        for domain,cmd in manifest['commands'].items():
            log=(a.out/(domain+'.log')).open('w');logs.append(log)
            processes.append((domain,subprocess.Popen(cmd,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)))
        for domain,proc in processes:
            code=proc.wait();path=a.out/domain/'manifest.json'
            batch=json.loads(path.read_text()) if path.exists() else {}
            manifest['batches'][domain]={'exit_code':code,'complete':bool(code==0 and batch.get('complete')),
                'successes':batch.get('successes'),'criteria_met':batch.get('simulation_batch_criteria_met',False),
                'manifest_sha256':sha(path) if path.exists() else None}
            (a.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        manifest['complete']=all(b['complete'] for b in manifest['batches'].values())
        manifest['simulation_criteria_met']=bool(manifest['complete'] and all(b['criteria_met'] for b in manifest['batches'].values()))
        if sha(ROOT/'evaluate_residual.py')!=manifest['evaluator_sha256']:
            raise RuntimeError('evaluator changed during the batches')
        (a.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        print(json.dumps(manifest['batches'],indent=2))
    finally:
        for _,proc in processes:
            if proc.poll() is None:proc.terminate();proc.wait()
        for log in logs:log.close()

if __name__=='__main__':main()
