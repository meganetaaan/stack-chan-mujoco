#!/usr/bin/env python3
"""Headless controlled experiment on the SAME saved policy (no training).

Baseline and post-slew LP40/LP80 run identical seeds and commands. Filters alter
runtime control dynamics intentionally; they are NOT claimed to be checkpoint-
compatible for resuming training, nor are successful-looking rollouts evidence
of sim-to-real safety. Results retain v3's raw-action quality criteria unchanged.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, os, sys, traceback
from copy import deepcopy
from pathlib import Path
for name in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS'):
    os.environ[name]='1'

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project',type=Path,default=Path('.'))
    p.add_argument('--checkpoint',type=Path,required=True)
    p.add_argument('--episodes',type=int,default=5)
    p.add_argument('--seed',type=int,default=20000)
    p.add_argument('--command',type=float,default=.02)
    p.add_argument('--taus-ms',default='0,40,80')
    p.add_argument('--out',type=Path,default=Path('outputs/control_probe'))
    args=p.parse_args()
    if args.episodes<1 or args.command<0:p.error('positive episodes and nonnegative command required')
    taus=[float(v)/1000 for v in args.taus_ms.split(',')]
    if not taus or any(not (0<=v<=.5) for v in taus) or len(set(taus))!=len(taus):
        p.error('taus must be distinct finite values in 0..500 ms')
    if 0.0 not in taus:p.error('include tau=0 as the unmodified baseline')
    sys.path.insert(0,str(args.project.resolve()))
    expected=json.loads((Path(__file__).parent/'expected_source.json').read_text())
    for rel,digest in expected.items():
        path=args.project/rel
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:
            raise RuntimeError(f'Source differs from examined v3: {path}. Do not silently bypass this check.')
    import numpy as np, torch, mujoco
    from stable_baselines3 import PPO
    from stackchan_rl.env import StackChanEnv
    from stackchan_rl.actuation import bounded_target
    from stackchan_rl.spec import JOINT_NAMES
    from stackchan_rl.checkpoints import bundle_info,assert_interface,versions
    from stackchan_rl.config import save_json
    from stackchan_rl.evaluation import aggregate
    from control_probe import PostSlewLowPassBank
    torch.set_num_threads(1)
    folder,cfg,interface,meta=bundle_info(args.checkpoint)
    assert_interface(interface,cfg)
    if cfg['env']['walk_objective_version']!=3:
        raise ValueError('Use the v3 walk_refine checkpoint for this probe')
    cfg=deepcopy(cfg);cfg['env']['domain_randomization']=False
    agent=PPO.load(str(folder/'model.zip'),device='cpu')
    if args.out.exists() and any(args.out.iterdir()):
        raise FileExistsError(f'{args.out} is not empty; choose a fresh --out')
    args.out.mkdir(parents=True,exist_ok=True)
    report={'status':'IN_PROGRESS','checkpoint':str(folder),
            'checkpoint_sha256':hashlib.sha256((folder/'model.zip').read_bytes()).hexdigest(),
            'checkpoint_step':meta.get('num_timesteps'),'versions':versions(),
            'command_m_s':args.command,'seed':args.seed,'episodes_each':args.episodes,
            'original_config':cfg,'original_interface':interface,
            'physics_executed':False,'not_hardware_validation':True,
            'note':'DIAGNOSTIC CONTROL OVERRIDES; no model/policy/criteria edits, no training',
            'experiments':[]}
    try:
        for tau in taus:
            label='baseline' if tau==0 else f'post_slew_lp_{round(tau*1000)}ms'
            dest=args.out/label;dest.mkdir()
            summaries=[]
            env=StackChanEnv(cfg)
            if tau:
                env.bank=PostSlewLowPassBank(env.specification.motor,float(env.model.opt.timestep),
                                             env.e['target_slew_rad_s'],tau)
            try:
                for ep in range(args.episodes):
                    obs,_=env.reset(seed=args.seed+ep,options={'command_forward_m_s':args.command,
                                         'no_noise':False,'domain_randomization':False})
                    observations=[];means=[];actions=[];predictions=[];times=[]
                    delta_sq=np.zeros(10);n=0;previous_target=env.bank.filtered.copy()
                    contact_pairs=[]
                    with (dest/f'episode_{ep:03}.csv').open('w',newline='',encoding='utf-8') as f:
                        def row():
                            out=env.trajectory_row();s=env.last_snapshot
                            out['self_contact_force_N']=float(s.get('self_contact_force_N',0))
                            for i,j in enumerate(JOINT_NAMES):
                                out[j+'_velocity_rad_s']=float(s['qd'][i])
                                out[j+'_delayed_target_rad']=float(env.bank.delayed[i])
                            for i,side in enumerate(('left','right')):
                                for k,axis in enumerate(('x','y','z')):
                                    out[f'{side}_sole_{axis}_m']=float(s['foot_xyz'][i,k])
                            return out
                        first=row();writer=csv.DictWriter(f,fieldnames=list(first));writer.writeheader();writer.writerow(first)
                        while True:
                            # Store the exact network inputs. No observation is synthesized
                            # later from numerical derivatives of trajectory CSV.
                            observations.append(obs.copy());times.append(float(env.data.time))
                            with torch.no_grad():
                                tensor,_=agent.policy.obs_to_tensor(obs)
                                mean=agent.policy.get_distribution(tensor).distribution.mean.cpu().numpy()[0]
                            action,_=agent.predict(obs,deterministic=True)
                            means.append(mean.copy());actions.append(action.copy())
                            predictions.append(bounded_target(action,env.home_joints,env.specification.limits,env.e))
                            obs,_,terminated,truncated,info=env.step(action)
                            report["physics_executed"]=True
                            if env.steps*env.dt>=env.e['measurement_start_s']:
                                delta_sq+=(env.bank.filtered-previous_target)**2;n+=1
                            previous_target=env.bank.filtered.copy();writer.writerow(row())
                            if terminated:
                                force=np.zeros(6)
                                for k in range(env.data.ncon):
                                    c=env.data.contact[k]
                                    if env.floor_id in (c.geom1,c.geom2):continue
                                    mujoco.mj_contactForce(env.model,env.data,k,force)
                                    if np.linalg.norm(force[:3])>=env.e['self_contact_threshold_N']:
                                        contact_pairs.append({'geom1':env.model.geom(c.geom1).name,
                                                              'geom2':env.model.geom(c.geom2).name,
                                                              'force_N':float(np.linalg.norm(force[:3])),
                                                              'distance_m':float(c.dist),
                                                              'time_s':float(env.data.time)})
                            if terminated or truncated:
                                summary=info['episode_summary']
                                summary.update(seed=args.seed+ep,episode_limit_s=cfg['env']['episode_seconds'],
                                               no_noise=False,control_probe_time_constant_s=tau,
                                               target_delta_rms_rad_each=np.sqrt(delta_sq/max(1,n)).tolist(),
                                               terminal_self_contact_pairs=contact_pairs)
                                summaries.append(summary);report['physics_executed']=True
                                break
                    np.savez_compressed(dest/f'episode_{ep:03}_policy.npz',
                                        observations=np.asarray(observations),raw_means=np.asarray(means),
                                        actions=np.asarray(actions),bounded_targets=np.asarray(predictions),
                                        time_s=np.asarray(times))
                    save_json(dest/f'episode_{ep:03}.json',summary)
                    print(f'{label} ep={ep} forward={summary["forward_m"]:.3f}m '
                          f'landings={summary["valid_landings"]} '
                          f'pitch={summary.get("pitch_rate_rms_rad_s",float("nan")):.3f} '
                          f'action_delta={summary.get("action_delta_rms",float("nan")):.3f} '
                          f'target_delta={float(np.sqrt(np.mean(delta_sq/max(1,n)))):.5f}rad '
                          f'reason={summary["failure_reason"]}',flush=True)
                    save_json(args.out/'partial.json',{**report,'current_experiment':label,'completed_episodes_current':summaries})
            finally:
                env.close()
            result=aggregate(summaries,3,physics_executed=True)
            result['label']=label;result['runtime_control_override']={'kind':'post_slew_lowpass','time_constant_s':tau}
            result['target_delta_rms_rad_mean']=float(np.mean([np.sqrt(np.mean(np.square(s['target_delta_rms_rad_each']))) for s in summaries]))
            report['experiments'].append(result)
        baseline=next(x for x in report['experiments'] if x['label']=='baseline')
        # Descriptive comparison only: never automatically deploy/overwrite a checkpoint.
        report['comparisons']=[]
        for exp in report['experiments']:
            report['comparisons'].append({'label':exp['label'],
                'forward_m_mean':exp['mean_forward_m'],'forward_change_m':exp['mean_forward_m']-baseline['mean_forward_m'],
                'survival_s_mean':exp['mean_duration_s'],'valid_landings_mean':exp['mean_valid_landings'],
                'target_delta_rms_rad_mean':exp['target_delta_rms_rad_mean'],
                'raw_action_delta_rms':exp['mean_quality'].get('action_delta_rms'),
                'pitch_rate_rms_rad_s':exp['mean_quality'].get('pitch_rate_rms_rad_s'),
                'failure_counts':exp['failure_counts']})
        report['status']='COMPLETE_DIAGNOSTIC_NOT_TRAINING'
        save_json(args.out/'comparison.json',report)
        if (args.out/'partial.json').exists():(args.out/'partial.json').unlink()
        print(json.dumps(report['comparisons'],ensure_ascii=False,indent=2));print((args.out/'comparison.json').resolve())
    except BaseException as exc:
        report['status']='INTERRUPTED' if isinstance(exc,KeyboardInterrupt) else 'ERROR'
        report['error']=str(exc);save_json(args.out/'error.json',report)
        raise
    return 0

if __name__=='__main__':
    raise SystemExit(main())
