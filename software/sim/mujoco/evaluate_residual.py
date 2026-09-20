#!/usr/bin/env python3
"""Frozen-policy R6 development/acceptance batches, including failed trials."""
import os
for name in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[name]='1'
import argparse
from concurrent.futures import ProcessPoolExecutor,as_completed
import json
import importlib.metadata
import platform
import multiprocessing
from pathlib import Path
import numpy as np
import torch
from stable_baselines3 import PPO
from stackchan_rl.residual import sha
from stackchan_rl.r6_factory import make_env


def canonical(value):return json.dumps(value,sort_keys=True)


def run_trial(job):
    checkpoint,config,out,seed,domain,controller=job
    torch.set_num_threads(1)
    out=Path(out);out.mkdir()
    env=make_env(config,record=True)
    interface=json.loads((Path(checkpoint)/'interface.json').read_text())
    if canonical(interface)!=canonical(env.fingerprint):raise ValueError('checkpoint interface/source mismatch')
    policy=None if controller=='zero' else PPO.load(Path(checkpoint)/('initial_policy' if controller=='initial' else 'policy'),device='cpu')
    obs,info=env.reset(seed=seed,options={'randomize':domain=='randomized'})
    reward=0.;done=False
    while not done:
        action=np.zeros(10) if policy is None else policy.predict(obs,deterministic=True)[0]
        obs,r,terminated,truncated,info=env.step(action);reward+=r;done=terminated or truncated
    # A full scheduled run is required: a 10 m crossing alone cannot conceal a
    # later collision during stopping. Numerical time tolerance is 1 ns.
    success=bool(info['failure'] is None and info['time_s']>=109.5-1e-9 and
        info['crossing_time_s'] is not None and info['crossing_time_s']<=100. and
        min(info['valid_landings'])>=20)
    env.save_trajectory(out/'states.npz')
    report={'schema':'r6-residual-evaluation-v1','domain':domain,'seed':seed,'controller':controller,
        'hardware_tested':False,'simulation_trial_pass':success,'reward':reward,**info,
        'trajectory_sha256':sha(out/'states.npz'),'interface':env.fingerprint,
        'action_rms':np.sqrt(np.mean(np.asarray(env.actions)**2,axis=0)).tolist(),
        'external_root_forces_used':False}
    (out/'report.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    env.close()
    return {'trial':out.name,**{k:report[k] for k in ('seed','simulation_trial_pass','failure','time_s',
            'forward_m','crossing_time_s','valid_landings','action_rms')},'report_sha256':sha(out/'report.json')}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--checkpoint',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--domain',choices=('fixed','randomized'),required=True)
    p.add_argument('--controller',choices=('trained','initial','zero'),default='trained')
    p.add_argument('--episodes',type=int,default=20)
    p.add_argument('--seed',type=int,required=True)
    p.add_argument('--duration',type=float,default=109.5)
    p.add_argument('--workers',type=int,default=4)
    p.add_argument('--purpose',choices=('development','acceptance'),default='development')
    args=p.parse_args()
    if args.episodes<1 or args.workers<1:p.error('positive episodes and workers required')
    if args.purpose=='acceptance' and (args.episodes!=20 or args.controller!='trained' or args.duration!=109.5):
        p.error('acceptance requires 20 trained-policy trials with full 109.5 second runs')
    if args.out.exists():p.error('use a new output directory')
    config=json.loads((args.checkpoint/'config.json').read_text());config['episode_s']=args.duration
    config['randomize']=args.domain=='randomized'
    policy_path=args.checkpoint/('initial_policy.zip' if args.controller=='initial' else 'policy.zip')
    if args.controller!='zero' and not policy_path.is_file():p.error('missing policy')
    if args.controller=='trained':
        training=json.loads((args.checkpoint/'training_result.json').read_text())
        if not training.get('trained') or training.get('policy_sha256')!=sha(policy_path):
            p.error('trained-policy provenance mismatch')
        if training.get('training_config_sha256',sha(args.checkpoint/'config.json'))!=sha(args.checkpoint/'config.json'):
            p.error('training config hash mismatch')
    args.out.mkdir(parents=True)
    (args.out/'config.json').write_text(json.dumps(config,indent=2)+'\n')
    manifest={'schema':'r6-residual-batch-v1','purpose':args.purpose,'domain':args.domain,
        'runtime':{'python':platform.python_version(),'packages':{k:importlib.metadata.version(k) for k in ('mujoco','numpy','gymnasium','stable-baselines3','torch')}},
        'controller':args.controller,'expected_trials':args.episodes,'seeds':list(range(args.seed,args.seed+args.episodes)),
        'policy_sha256':sha(policy_path) if args.controller!='zero' else None,'evaluator_sha256':sha(__file__),
        'training_config_sha256':sha(args.checkpoint/'config.json'),'evaluation_config_sha256':sha(args.out/'config.json'),
        'required_successes':20 if args.domain=='fixed' else 18,'complete':False,'successes':0,'results':[],
        'simulation_batch_criteria_met':False,'hardware_acceptance':False}
    (args.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    jobs=[(str(args.checkpoint.resolve()),config,str((args.out/f'trial_{i:02d}').resolve()),seed,args.domain,args.controller)
          for i,seed in enumerate(manifest['seeds'])]
    results=[]
    with ProcessPoolExecutor(max_workers=args.workers,mp_context=multiprocessing.get_context('spawn')) as pool:
        for future in as_completed([pool.submit(run_trial,j) for j in jobs]):
            result=future.result();results.append(result)
            manifest['results']=sorted(results,key=lambda x:x['trial'])
            manifest['successes']=sum(x['simulation_trial_pass'] for x in results)
            temp=args.out/'manifest.tmp';temp.write_text(json.dumps(manifest,indent=2)+'\n');temp.replace(args.out/'manifest.json')
            print(json.dumps(result),flush=True)
    manifest['complete']=True
    manifest['simulation_batch_criteria_met']=bool(args.purpose=='acceptance' and len(results)==20 and manifest['successes']>=manifest['required_successes'])
    (args.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({k:v for k,v in manifest.items() if k!='results'},indent=2))


if __name__=='__main__':main()
