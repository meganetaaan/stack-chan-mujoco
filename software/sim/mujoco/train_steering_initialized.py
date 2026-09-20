#!/usr/bin/env python3
"""Initialize neural steering from measured authority, then refine with PPO.

Initialization targets are a transparent analytic teacher on recorded simulator
observations. Acceptance uses only the learned neural policy and real dynamics.
No analytic steering feedback is added at evaluation/runtime.
"""
import os
for k in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS'):os.environ[k]='1'
import argparse
import copy
import importlib.metadata
import json
from pathlib import Path
import torch
import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import SubprocVecEnv
from stable_baselines3.common.monitor import Monitor
from stackchan_rl.residual import ROOT,sha,runtime_xml
from stackchan_rl.r6_factory import make_env
import mujoco


def teacher(parent,obs):
    with torch.no_grad():
        action=parent.policy.action_net(parent.policy.mlp_extractor.forward_actor(obs)).clone()
        support=torch.abs(obs[:,62]-obs[:,63])
        # Measured differential-knee gain is about 4.5 rad/s per rad.
        # Observation gyro is divided by 10; action is multiplied by .02 rad.
        correction=-(1.5*obs[:,65]+.45*obs[:,67]+2.5*obs[:,35])*support
        correction=torch.clamp(correction,-.6,.6)
        action[:,2]+=correction;action[:,7]-=correction
        return torch.clamp(action,-.95,.95)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--parent',type=Path,required=True);p.add_argument('--dataset',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);p.add_argument('--seed',type=int,default=20260923)
    p.add_argument('--bc-steps',type=int,default=8000);p.add_argument('--ppo-steps',type=int,default=32768)
    a=p.parse_args()
    if a.out.exists():p.error('use a new output directory')
    c=json.loads((a.parent/'config.json').read_text());c['design']='assets/r6_base_collisions'
    c['episode_s']=30.;t=c['training'];t.update(seed=a.seed,total_timesteps=a.ppo_steps,learning_rate=.0001,n_epochs=5)
    patch=json.loads((ROOT/c['design']/'BASE_COLLISION_PATCH.json').read_text())
    old_interface=json.loads((a.parent/'interface.json').read_text())
    if patch['source_model_sha256']!=old_interface['model_sha256']:raise ValueError('unsupported parent/model transition')
    old_config=json.loads((a.parent/'config.json').read_text())
    old=mujoco.MjModel.from_xml_string(runtime_xml(ROOT/old_config['design']/'models/scene.xml'))
    new=mujoco.MjModel.from_xml_string(runtime_xml(ROOT/c['design']/'models/scene.xml'))
    for key in ['body_mass','body_inertia','body_ipos','body_iquat','jnt_range','jnt_axis','jnt_pos',
                'actuator_ctrlrange','actuator_forcerange','actuator_gear','dof_damping','dof_frictionloss','dof_armature']:
        if not np.array_equal(getattr(old,key),getattr(new,key)):raise ValueError('unexpected model change: '+key)
    if new.ngeom-old.ngeom!=22:raise ValueError('unexpected added geometry count')
    dataset_manifest=[];train=[];valid=[]
    for domain in ('fixed','randomized'):
        for trial in sorted((a.dataset/domain).glob('trial_*')):
            report=json.loads((trial/'report.json').read_text());path=trial/'states.npz'
            if sha(path)!=report['trajectory_sha256']:raise ValueError('dataset state hash mismatch')
            obs=np.load(path,allow_pickle=False)['observation'][:-1]
            if obs.ndim!=2 or obs.shape[1]!=70 or not np.isfinite(obs).all():raise ValueError('expected finite 70D observations')
            held_out=int(trial.name.split('_')[-1])>=18
            (valid if held_out else train).append(obs)
            dataset_manifest.append({'path':str(path),'sha256':sha(path),'rows':len(obs),'held_out_for_function_fit':held_out})
    if len(dataset_manifest)!=40:raise ValueError('all 40 recorded trials required')
    train=torch.as_tensor(np.concatenate(train),dtype=torch.float32)
    valid=torch.as_tensor(np.concatenate(valid),dtype=torch.float32)
    torch.set_num_threads(1)
    # Load the parent BEFORE constructing/seeding the new learner.
    parent=PPO.load(a.parent/'policy',device='cpu')
    a.out.mkdir(parents=True)
    probe=make_env(c)
    (a.out/'config.json').write_text(json.dumps(c,indent=2)+'\n')
    (a.out/'interface.json').write_text(json.dumps(probe.fingerprint,indent=2)+'\n');probe.close()
    (a.out/'initialization_dataset.json').write_text(json.dumps(dataset_manifest,indent=2)+'\n')
    runtime={'seed':a.seed,'parent_policy_sha256':sha(a.parent/'policy.zip'),
        'script_sha256':sha(__file__),'initialization':'analytic differential-knee steering teacher fitted on real recorded observations; fresh critic',
        'teacher_action_correction':'clamp(-(1.5*sin_heading+.45*lateral_m+.25*gyro_z_rad_s)*support_asymmetry, +/-.6), left knee plus, right knee minus',
        'runtime_analytic_feedback':False,'bc_steps':a.bc_steps,'ppo_steps':a.ppo_steps,
        'rng_order':'load parent, construct new PPO with requested seed, use separate NumPy generator for BC minibatches',
        'packages':{k:importlib.metadata.version(k) for k in ('mujoco','numpy','gymnasium','stable-baselines3','torch')}}
    (a.out/'runtime.json').write_text(json.dumps(runtime,indent=2)+'\n')
    env=SubprocVecEnv([lambda i=i:Monitor(make_env(c),filename=str(a.out/f'monitor_{i}')) for i in range(t['n_envs'])],start_method='spawn')
    try:
        model=PPO('MlpPolicy',env,seed=a.seed,device='cpu',verbose=1,n_steps=t['n_steps'],batch_size=t['batch_size'],
            learning_rate=t['learning_rate'],n_epochs=t['n_epochs'],gamma=t['gamma'],gae_lambda=t['gae_lambda'],
            policy_kwargs={'net_arch':dict(pi=[64,64],vf=[64,64]),'log_std_init':-3.2})
        model.policy.mlp_extractor.policy_net.load_state_dict(parent.policy.mlp_extractor.policy_net.state_dict())
        model.policy.action_net.load_state_dict(parent.policy.action_net.state_dict())
        actor=list(model.policy.mlp_extractor.policy_net.parameters())+list(model.policy.action_net.parameters())
        opt=torch.optim.Adam(actor,lr=.001);rng=np.random.default_rng(a.seed)
        with torch.no_grad():train_targets=teacher(parent,train);valid_targets=teacher(parent,valid)
        for step in range(a.bc_steps):
            ix=rng.integers(0,len(train),size=256);obs=train[ix]
            prediction=model.policy.action_net(model.policy.mlp_extractor.forward_actor(obs))
            loss=torch.mean((prediction-train_targets[ix])**2)
            opt.zero_grad();loss.backward();torch.nn.utils.clip_grad_norm_(actor,1.);opt.step()
            if (step+1)%1000==0:print('BC',step+1,'loss',float(loss.detach()),flush=True)
        with torch.no_grad():
            prediction=model.policy.action_net(model.policy.mlp_extractor.forward_actor(valid))
            error=(prediction-valid_targets).numpy()
        fit={'scope':'held-out trial observations for teacher-function fit, NOT gait acceptance',
            'rms_action_error_by_joint':np.sqrt(np.mean(error**2,axis=0)).tolist(),
            'p99_absolute_action_error':float(np.quantile(np.abs(error),.99)),'rows':len(valid)}
        (a.out/'initialization_fit.json').write_text(json.dumps(fit,indent=2)+'\n')
        model.save(a.out/'initial_policy')
        if max(fit['rms_action_error_by_joint'])>.03 or fit['p99_absolute_action_error']>.1:
            raise RuntimeError('teacher approximation insufficient; PPO was not started')
        model.learn(total_timesteps=a.ppo_steps);model.save(a.out/'policy')
        (a.out/'training_result.json').write_text(json.dumps({'timesteps':model.num_timesteps,
            'initial_policy_sha256':sha(a.out/'initial_policy.zip'),'policy_sha256':sha(a.out/'policy.zip'),
            'training_config_sha256':sha(a.out/'config.json'),'trained':True,'acceptance_tested':False},indent=2)+'\n')
    finally:env.close()

if __name__=='__main__':main()
