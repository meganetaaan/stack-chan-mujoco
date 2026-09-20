#!/usr/bin/env python3
"""Continue residual PPO with unchanged action/observation and plant interface."""
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
    p.add_argument('--checkpoint',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--seed',type=int,required=True);p.add_argument('--timesteps',type=int,default=98304)
    p.add_argument('--episode-s',type=float,default=30.);p.add_argument('--learning-rate',type=float,default=.0003)
    a=p.parse_args()
    if a.out.exists():p.error('use a new output directory')
    c=json.loads((a.checkpoint/'config.json').read_text());c['episode_s']=a.episode_s
    t=c['training'];t.update(seed=a.seed,total_timesteps=a.timesteps,learning_rate=a.learning_rate,n_epochs=10)
    probe=ResidualEnv(c)
    if json.dumps(probe.fingerprint,sort_keys=True)!=json.dumps(json.loads((a.checkpoint/'interface.json').read_text()),sort_keys=True):
        raise ValueError('cannot continue a different environment interface')
    a.out.mkdir(parents=True);torch.set_num_threads(1)
    (a.out/'config.json').write_text(json.dumps(c,indent=2)+'\n')
    (a.out/'interface.json').write_text(json.dumps(probe.fingerprint,indent=2)+'\n');probe.close()
    metadata={'python':platform.python_version(),'packages':{x:importlib.metadata.version(x) for x in
        ('mujoco','numpy','gymnasium','stable-baselines3','torch')},'device':'cpu','seed':t['seed'],
        'training_script_sha256':sha(__file__),'parent_policy_sha256':sha(a.checkpoint/'policy.zip'),
        'git_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        'scope':'continued residual RL; initial_policy.zip is the parent trained policy, not random initialization'}
    (a.out/'runtime.json').write_text(json.dumps(metadata,indent=2)+'\n')
    env=SubprocVecEnv([lambda i=i:Monitor(ResidualEnv(c),filename=str(a.out/f'monitor_{i}')) for i in range(t['n_envs'])],start_method='spawn')
    try:
        model=PPO.load(a.checkpoint/'policy',env=env,device='cpu',custom_objects={'learning_rate':a.learning_rate})
        model.set_random_seed(a.seed);model.n_epochs=t['n_epochs'];model.verbose=1
        model.save(a.out/'initial_policy')
        parent_steps=model.num_timesteps
        model.learn(total_timesteps=a.timesteps,reset_num_timesteps=False)
        model.save(a.out/'policy')
        (a.out/'training_result.json').write_text(json.dumps({'timesteps':model.num_timesteps,
            'additional_timesteps':model.num_timesteps-parent_steps,
            'initial_policy_sha256':sha(a.out/'initial_policy.zip'),'policy_sha256':sha(a.out/'policy.zip'),
            'trained':True,'acceptance_tested':False},indent=2)+'\n')
    finally:env.close()

if __name__=='__main__':main()
