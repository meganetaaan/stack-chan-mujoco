#!/usr/bin/env python3
"""Explicit policy transfer to mounted-battery physics followed by PPO training."""
import os
for key in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS'):
    os.environ[key]='1'
import argparse
import importlib.metadata
import json
from pathlib import Path
import platform
import torch
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import SubprocVecEnv
from stable_baselines3.common.monitor import Monitor
from stackchan_rl.r6_factory import make_env
from stackchan_rl.residual import sha


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--checkpoint',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--seed',type=int,default=20260924)
    a=p.parse_args()
    if a.out.exists(): p.error('new output directory required')
    c=json.loads((a.checkpoint/'config.json').read_text())
    if c['schema']!='r6-residual-heading-v2': raise ValueError('requires heading policy')
    parent_result=json.loads((a.checkpoint/'training_result.json').read_text())
    if not parent_result['trained'] or parent_result['policy_sha256']!=sha(a.checkpoint/'policy.zip'):
        raise ValueError('parent policy provenance mismatch')
    c['design']='assets/r6_mounted_battery'
    c['training'].update(seed=a.seed,total_timesteps=32768,learning_rate=.0001,n_epochs=5)
    c['episode_s']=30.
    a.out.mkdir(parents=True);torch.set_num_threads(1)
    probe=make_env(c)
    (a.out/'config.json').write_text(json.dumps(c,indent=2)+'\n')
    (a.out/'interface.json').write_text(json.dumps(probe.fingerprint,indent=2)+'\n');probe.close()
    # Load first: fresh PPO construction below resets the RNGs after deserialization.
    parent=PPO.load(a.checkpoint/'policy',device='cpu')
    t=c['training']
    env=SubprocVecEnv([lambda i=i:Monitor(make_env(c),filename=str(a.out/f'monitor_{i}')) for i in range(t['n_envs'])],start_method='spawn')
    try:
        model=PPO('MlpPolicy',env,seed=a.seed,device='cpu',verbose=1,
            policy_kwargs=parent.policy_kwargs,n_steps=t['n_steps'],batch_size=t['batch_size'],
            learning_rate=t['learning_rate'],n_epochs=t['n_epochs'],gamma=t['gamma'],gae_lambda=t['gae_lambda'])
        model.policy.load_state_dict(parent.policy.state_dict())
        model.save(a.out/'initial_policy')
        runtime={'scope':'Parent learned weights transferred to changed plant; fresh optimizer and PPO training',
                 'parent_policy_sha256':sha(a.checkpoint/'policy.zip'),'parent_config_sha256':sha(a.checkpoint/'config.json'),
                 'training_source_sha256':sha(__file__),'training_config_sha256':sha(a.out/'config.json'),
                 'seed':a.seed,'rng_order':'parent deserialization before fresh seeded PPO construction',
                 'python':platform.python_version(),'packages':{k:importlib.metadata.version(k) for k in ('mujoco','numpy','gymnasium','stable-baselines3','torch')}}
        (a.out/'runtime.json').write_text(json.dumps(runtime,indent=2)+'\n')
        model.learn(total_timesteps=t['total_timesteps'])
        model.save(a.out/'policy')
        (a.out/'training_result.json').write_text(json.dumps({'trained':True,'acceptance_tested':False,
            'timesteps':model.num_timesteps,'policy_sha256':sha(a.out/'policy.zip'),
            'initial_policy_sha256':sha(a.out/'initial_policy.zip'),
            'training_config_sha256':sha(a.out/'config.json')},indent=2)+'\n')
    finally: env.close()


if __name__=='__main__': main()
