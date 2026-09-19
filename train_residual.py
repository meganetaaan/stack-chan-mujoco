#!/usr/bin/env python3
"""Train a separately versioned R6 residual PPO policy; save exact configuration."""
import os
for name in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[name]='1'
import argparse
import importlib.metadata
import json
from pathlib import Path
import platform
import subprocess
import torch
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import SubprocVecEnv
from stable_baselines3.common.monitor import Monitor
from stackchan_rl.residual import ResidualEnv,sha


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config',type=Path,default=Path('configs/r6/residual.json'))
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--timesteps',type=int)
    args=p.parse_args()
    c=json.loads(args.config.read_text());t=c['training']
    if args.timesteps is not None:t['total_timesteps']=args.timesteps
    if args.out.exists():p.error('use a new output directory')
    args.out.mkdir(parents=True)
    torch.set_num_threads(1)
    (args.out/'config.json').write_text(json.dumps(c,indent=2)+'\n')
    probe=ResidualEnv(c)
    (args.out/'interface.json').write_text(json.dumps(probe.fingerprint,indent=2)+'\n');probe.close()
    metadata={'python':platform.python_version(),'packages':{x:importlib.metadata.version(x) for x in
        ('mujoco','numpy','gymnasium','stable-baselines3','torch')},'device':'cpu','seed':t['seed'],
        'training_script_sha256':sha(__file__),
        'git_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        'scope':'trained residual on kinematic prior; not acceptance evidence'}
    (args.out/'runtime.json').write_text(json.dumps(metadata,indent=2)+'\n')
    env=SubprocVecEnv([lambda i=i:Monitor(ResidualEnv(c),filename=str(args.out/f'monitor_{i}')) for i in range(t['n_envs'])],start_method='spawn')
    try:
        model=PPO('MlpPolicy',env,seed=t['seed'],device='cpu',verbose=1,
            n_steps=t['n_steps'],batch_size=t['batch_size'],learning_rate=t['learning_rate'],
            n_epochs=t['n_epochs'],gamma=t['gamma'],gae_lambda=t['gae_lambda'],
            policy_kwargs={'net_arch':dict(pi=[64,64],vf=[64,64]),'log_std_init':t['initial_log_std']})
        model.save(args.out/'initial_policy')
        model.learn(total_timesteps=t['total_timesteps'])
        model.save(args.out/'policy')
        (args.out/'training_result.json').write_text(json.dumps({'timesteps':model.num_timesteps,
            'initial_policy_sha256':sha(args.out/'initial_policy.zip'),'policy_sha256':sha(args.out/'policy.zip'),
            'trained':True,'acceptance_tested':False},indent=2)+'\n')
    finally:env.close()


if __name__=='__main__':main()
