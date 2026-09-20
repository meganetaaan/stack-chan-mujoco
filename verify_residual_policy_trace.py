#!/usr/bin/env python3
"""Verify that recorded actions come from the published trained policy."""
import os
for key in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS'):os.environ[key]='1'
import argparse
import json
from pathlib import Path
import numpy as np
import torch
from stable_baselines3 import PPO
from stackchan_rl.residual import sha


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--checkpoint',type=Path,required=True)
    p.add_argument('--trial',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    if a.out.exists():p.error('use a new output file')
    report=json.loads((a.trial/'report.json').read_text())
    if report['controller']!='trained':raise ValueError('requires trained-policy trajectory')
    trace_path=a.trial/'states.npz'
    if sha(trace_path)!=report['trajectory_sha256']:raise ValueError('trajectory hash mismatch')
    torch.set_num_threads(1)
    model=PPO.load(a.checkpoint/'policy',device='cpu');initial=PPO.load(a.checkpoint/'initial_policy',device='cpu')
    with np.load(trace_path,allow_pickle=False) as trace:
        obs=trace['observation'][:-1];actions=trace['action']
        predicted=model.predict(obs,deterministic=True)[0]
        initial_actions=initial.predict(obs,deterministic=True)[0]
    error=float(np.max(np.abs(actions-predicted)))
    if error>1e-6:raise ValueError(f'policy does not reproduce actions: {error}')
    change=float(np.sqrt(np.mean((predicted-initial_actions)**2)))
    if change<1e-6:raise ValueError('no measurable change from initial policy')
    config=json.loads((a.checkpoint/'config.json').read_text())
    result={'policy_sha256':sha(a.checkpoint/'policy.zip'),'initial_policy_sha256':sha(a.checkpoint/'initial_policy.zip'),
        'states_sha256':sha(trace_path),'actions_checked':len(actions),'maximum_action_replay_error':error,
        'action_rms':np.sqrt(np.mean(actions**2,axis=0)).tolist(),
        'joint_residual_rms_rad':(config['residual_scale_rad']*np.sqrt(np.mean(actions**2,axis=0))).tolist(),
        'rms_action_change_from_initial':change,
        'scope':'action provenance and measurable learning; not proof of improvement over the reference',
        'verification_source_sha256':sha(__file__)}
    a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

if __name__=='__main__':main()
