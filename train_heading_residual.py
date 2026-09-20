#!/usr/bin/env python3
"""Train heading-aware residual PPO, optionally warm-starting a 65D policy."""
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
from stackchan_rl.residual import sha
from stackchan_rl.residual_heading import HeadingResidualEnv


def transfer_policy(parent,model):
    """Zero new input columns, preserving the parent function on the first 65."""
    source=parent.policy.state_dict();target=model.policy.state_dict()
    expanded=[]
    for key,value in target.items():
        old=source[key]
        if value.shape==old.shape:target[key]=old.clone()
        elif key in ('mlp_extractor.policy_net.0.weight','mlp_extractor.value_net.0.weight') and value.shape==(64,70) and old.shape==(64,65):
            value.zero_();value[:,:65]=old;target[key]=value;expanded.append(key)
        else:raise ValueError(f'unsupported transfer shape: {key}')
    if len(expanded)!=2:raise ValueError('expected exactly actor and critic input expansions')
    model.policy.load_state_dict(target)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config',type=Path,default=Path('configs/r6/heading_residual.json'))
    p.add_argument('--parent',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();c=json.loads(a.config.read_text());t=c['training']
    if a.out.exists():p.error('use a new output directory')
    parent_config=json.loads((a.parent/'config.json').read_text())
    for k in ('command_m_s','policy_dt_s','residual_scale_rad','slew_rad_s','lowpass_s','protection'):
        if c[k]!=parent_config[k]:raise ValueError(f'transfer changes control semantics: {k}')
    probe=HeadingResidualEnv(c)
    parent_interface=json.loads((a.parent/'interface.json').read_text())
    for k in ('model_sha256','robot_sha256','reference_sha256'):
        if probe.fingerprint[k]!=parent_interface[k]:raise ValueError(f'transfer changes model/reference: {k}')
    a.out.mkdir(parents=True);torch.set_num_threads(1)
    (a.out/'config.json').write_text(json.dumps(c,indent=2)+'\n')
    (a.out/'interface.json').write_text(json.dumps(probe.fingerprint,indent=2)+'\n');probe.close()
    runtime={'python':platform.python_version(),'packages':{x:importlib.metadata.version(x) for x in
        ('mujoco','numpy','gymnasium','stable-baselines3','torch')},'device':'cpu','seed':t['seed'],
        'git_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        'training_script_sha256':sha(__file__),'parent_policy_sha256':sha(a.parent/'policy.zip'),
        'initialization':'parent actor/critic, new observation input columns zero; fresh optimizer',
        'heading_sensor':'noisy external reference, not an IMU-only estimate'}
    (a.out/'runtime.json').write_text(json.dumps(runtime,indent=2)+'\n')
    env=SubprocVecEnv([lambda i=i:Monitor(HeadingResidualEnv(c),filename=str(a.out/f'monitor_{i}')) for i in range(t['n_envs'])],start_method='spawn')
    try:
        model=PPO('MlpPolicy',env,seed=t['seed'],device='cpu',verbose=1,n_steps=t['n_steps'],
            batch_size=t['batch_size'],learning_rate=t['learning_rate'],n_epochs=t['n_epochs'],
            gamma=t['gamma'],gae_lambda=t['gae_lambda'],
            policy_kwargs={'net_arch':dict(pi=[64,64],vf=[64,64]),'log_std_init':t['initial_log_std']})
        parent=PPO.load(a.parent/'policy',device='cpu');transfer_policy(parent,model)
        model.save(a.out/'initial_policy');model.learn(total_timesteps=t['total_timesteps']);model.save(a.out/'policy')
        (a.out/'training_result.json').write_text(json.dumps({'timesteps':model.num_timesteps,
            'initial_policy_sha256':sha(a.out/'initial_policy.zip'),'policy_sha256':sha(a.out/'policy.zip'),
            'training_config_sha256':sha(a.out/'config.json'),'trained':True,'acceptance_tested':False},indent=2)+'\n')
    finally:env.close()

if __name__=='__main__':main()
