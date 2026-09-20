#!/usr/bin/env python3
"""Drive a 12-axis candidate through actual constrained servo physics.

Development only: drive a ten-axis reference with zero yaw, or an explicit q12
reference. Neither mode substitutes for the frozen maneuver acceptance test.
"""
import argparse
import gzip
import json
from pathlib import Path
from types import SimpleNamespace
import mujoco
import numpy as np
from stackchan_rl.residual import ResidualEnv,SaturationProtection,STATE_SPEC,runtime_xml,sha
from stackchan_rl.actuation import PostSlewLowPassBank
from stackchan_rl.walk_events import WalkEventTracker
from stackchan_rl.config import DEFAULT
from stackchan_rl.maneuver_protocol import validate,command_at,score_motion
from stackchan_rl.candidate_variation import sample_parameters,apply_parameters


class JointProtection(SaturationProtection):
    def __init__(self,dt,cfg,count):
        super().__init__(dt,cfg)
        for name in ('streak','peak_streak','sum'):setattr(self,name,np.zeros(count,dtype=int))
        self.peak_duty=np.zeros(count)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--design',type=Path,required=True)
    p.add_argument('--reference',type=Path,default=Path('validation/plant_screen/aligned_reference.json.gz'))
    p.add_argument('--duration',type=float,default=6.)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--static-torque-scale',type=float,help='use 1 for a reference already recomputed at candidate mass')
    p.add_argument('--policy',type=Path,help='optional old ten-axis forward policy; developmental transfer only')
    p.add_argument('--seed',type=int,default=310501)
    p.add_argument('--yaw-kp',type=float,default=3.)
    p.add_argument('--yaw-kd',type=float,default=.065)
    p.add_argument('--ankle-kd',type=float,help='development damping for ankle pitch and roll; torque/speed caps unchanged')
    p.add_argument('--attitude-gain',type=float,default=0.)
    p.add_argument('--attitude-rate-gain',type=float,default=0.)
    p.add_argument('--attitude-axes',choices=['both','roll'],default='both')
    p.add_argument('--imu-delay-s',type=float,default=.02)
    p.add_argument('--protocol',type=Path,help='execute and score scheduled commands; development seeds only')
    p.add_argument('--randomize',action='store_true',help='apply baseline plant ranges to all twelve joints')
    a=p.parse_args()
    if a.randomize and a.policy:p.error('randomized legacy policy transfer is not implemented')
    if not np.isfinite(a.imu_delay_s) or not 0<=a.imu_delay_s<=.1:p.error('IMU delay must be in [0,.1] seconds')
    if a.randomize and a.static_torque_scale!=1:p.error('randomized trials require nominal reference feedforward: --static-torque-scale 1')
    if a.out.exists() or not np.isfinite(a.duration) or a.duration<=0:p.error('new output and positive finite duration required')
    if 217000<=a.seed<=217019 or 218000<=a.seed<=218019:p.error('reserved acceptance seed')
    if not np.isfinite([a.yaw_kp,a.yaw_kd]).all() or not 0<a.yaw_kp<=12 or not 0<=a.yaw_kd<=.3:
        p.error('candidate yaw gains require kp in (0,12] and kd in [0,.3]')
    if a.ankle_kd is not None and (not np.isfinite(a.ankle_kd) or not 0<=a.ankle_kd<=.3):p.error('ankle damping must be in [0,.3]')
    if not np.isfinite([a.attitude_gain,a.attitude_rate_gain]).all() or not 0<=a.attitude_gain<=2 or not 0<=a.attitude_rate_gain<=.3:
        p.error('attitude gains outside development bounds')
    with gzip.open(a.reference,'rt') as f:reference=json.load(f)
    protocol=None
    if a.protocol:
        protocol=json.loads(a.protocol.read_text());boundaries=validate(protocol)
        if a.duration>boundaries[-1]:p.error('duration exceeds schedule')
        for sample in reference:
            index,command=command_at(protocol,sample['time_s'])
            if sample.get('segment_index')!=index or not np.array_equal(sample.get('command'),command):
                raise ValueError('reference command differs from protocol')
    if a.duration>reference[-1]['time_s'] or not np.isclose(a.duration/.02,round(a.duration/.02)):
        p.error('duration must fit reference and a 20 ms sample')
    config=json.loads(Path('policies/r6_mounted_seed20260924/config.json').read_text())
    robot=json.loads((a.design/'robot.json').read_text())
    names=[item['name'] for item in json.loads((a.design/'models/joint_map.json').read_text())]
    m=mujoco.MjModel.from_xml_string(runtime_xml(a.design/'models/scene.xml'))
    d=mujoco.MjData(m)
    if (m.nq,m.nv,m.nu)!=(19,18,12) or m.neq or np.any(m.body_gravcomp) or not np.array_equal(m.opt.gravity,[0,0,-9.81]):
        raise ValueError('requires an unassisted twelve-axis floating robot')
    qadr=np.array([m.joint(name).qposadr[0] for name in names]);vadr=np.array([m.joint(name).dofadr[0] for name in names])
    aids=np.array([m.actuator(name+'_motor').id for name in names]);limits=np.array([m.joint(name).range for name in names])
    old_indices=np.array([i for i,name in enumerate(names) if not name.endswith('hip_yaw')])
    specs=[]
    for name in names:
        s=dict(robot['motor'])
        if name.split('_',1)[1] in robot['motor_overrides']['joint_types']:s.update(robot['motor_overrides'])
        specs.append(s)
    fields={'cap':'simulation_torque_cap_Nm','stall':'stall_torque_Nm','kp':'kp_Nm_rad','kd':'kd_Nm_s_rad','delay_s':'command_delay_s'}
    motor={k:np.array([s[v] for s in specs]) for k,v in fields.items()}
    motor['omega']=np.array([s['no_load_speed_rpm']*np.pi/30 for s in specs])
    yaw_indices=np.array([i for i,name in enumerate(names) if name.endswith('hip_yaw')])
    motor['kp'][yaw_indices]=a.yaw_kp;motor['kd'][yaw_indices]=a.yaw_kd
    if a.ankle_kd is not None:
        motor['kd'][[i for i,name in enumerate(names) if '_ankle_' in name]]=a.ankle_kd
    parameters=sample_parameters(config,np.random.default_rng(a.seed),a.randomize,m.geom_friction[m.geom('floor').id,0],12)
    motor=apply_parameters(m,d,motor,aids,m.body('base').id,parameters)
    mujoco.mj_resetDataKeyframe(m,d,0)
    d.qpos[:3]=np.array(reference[0]['base'])[:3,3];d.qpos[2]+=.0005
    initial=np.zeros(12);initial[old_indices]=reference[0]['q']
    if 'q12' in reference[0]:initial=np.asarray(reference[0]['q12'],dtype=float)
    if initial.shape!=(12,) or not np.isfinite(initial).all():raise ValueError('invalid initial joint reference')
    d.qpos[qadr]=initial+parameters['initial_joint_offsets_rad']
    mujoco.mj_forward(m,d)
    plant=SimpleNamespace(model=m,data=d,qadr=qadr,limits=limits,base=m.body('base').id,
                          floor=m.geom('floor').id,soles=np.array([m.geom('col_'+side+'_sole_TPU_0').id for side in ('left','right')]),
                          warnings=np.array([w.number for w in d.warning]),loads=np.zeros(2),force=np.zeros(6))
    bank=PostSlewLowPassBank(motor,m.opt.timestep,config['slew_rad_s'],config['lowpass_s']);bank.reset(d.qpos[qadr])
    protection=JointProtection(m.opt.timestep,config['protection'],12)
    tracker=WalkEventTracker(m.opt.timestep,DEFAULT['env'])
    if protocol:
        from stackchan_rl.maneuver_env import CommandWalkTracker
        tracker=CommandWalkTracker(tracker,len(protocol['segments']))
    start=d.xpos[plant.base].copy();failure=ResidualEnv._check_physics(plant)
    def state():
        array=np.empty(mujoco.mj_stateSize(m,STATE_SPEC));mujoco.mj_getState(m,d,array,STATE_SPEC);return array
    states=[state()];torques=[];targets=[];observations=[];actions=[];imu_observations=[]
    motion=[[float(d.time),*d.xpos[plant.base,:2],float(np.arctan2(d.xmat[plant.base,3],d.xmat[plant.base,0]))]]
    policy=None;view=None;previous_action=np.zeros(10)
    imu=None
    if a.attitude_gain or a.attitude_rate_gain:
        from stackchan_rl.attitude_observer import AttitudeObserver
        imu=AttitudeObserver(m,d,plant.base,parameters,a.seed+1000000,delay_s=a.imu_delay_s)
    if a.policy:
        from stackchan_rl.legacy_policy_view import LegacyPolicyView
        view=LegacyPolicyView(m,d,plant.base,qadr[old_indices],vadr[old_indices],reference,config,start,a.seed)
    if a.policy:
        from stable_baselines3 import PPO
        import torch
        torch.set_num_threads(1)
        policy=PPO.load(a.policy,device='cpu')
        if policy.observation_space.shape!=(70,) or policy.action_space.shape!=(10,):raise ValueError('requires 70-observation ten-action policy')
    baseline_mass=sum(x['mass_kg'] for x in json.loads(Path('assets/r6_mounted_battery/models/inertials.json').read_text()).values())
    torque_scale=float(m.body_mass.sum()/baseline_mass)
    if a.static_torque_scale is not None:
        if not np.isfinite(a.static_torque_scale) or not 0<a.static_torque_scale<=2:p.error('finite torque scale in (0,2] required')
        torque_scale=a.static_torque_scale
    substeps=round(.02/m.opt.timestep)
    if not np.isclose(substeps*m.opt.timestep,.02):raise ValueError('nonintegral control period')
    i=0
    while not failure and d.time<a.duration-1e-9:
        sample=reference[i]
        if protocol:
            tracker.segment_index=sample['segment_index']
            tracker.moving=bool(np.any(sample['command']))
        if abs(sample['time_s']-i*.02)>1e-9:raise ValueError('reference sample cadence mismatch')
        target=np.zeros(12)
        target[old_indices]=np.array(sample['q'])+np.array(sample['quasistatic_torque_Nm'])*torque_scale/motor['kp'][old_indices]
        if 'q12' in sample:
            q12=np.asarray(sample['q12'],dtype=float)
            if q12.shape!=(12,) or not np.isfinite(q12).all():raise ValueError('invalid twelve-axis reference')
            target=q12.copy()
            target[old_indices]+=np.array(sample['quasistatic_torque_Nm'])*torque_scale/motor['kp'][old_indices]
        action=np.zeros(10)
        if view is not None:
            obs=view.observe(i,bank.filtered[old_indices],previous_action)
            observations.append(obs.copy())
        if policy is not None:action,_=policy.predict(obs,deterministic=True)
        target[old_indices]+=config['residual_scale_rad']*action
        if a.attitude_gain or a.attitude_rate_gain:
            imu_obs=imu.read();imu_observations.append(imu_obs.copy())
            gravity=imu_obs[:3]
            angles=np.array([np.arctan2(-gravity[1],-gravity[2]),np.arcsin(np.clip(gravity[0],-1,1))])
            correction=a.attitude_gain*angles+a.attitude_rate_gain*imu_obs[3:5]
            if a.attitude_axes=='roll':correction[1]=0.
            correction=np.clip(correction,-.15,.15)
            for leg,weight in enumerate(sample['support']):
                target[old_indices[5*leg+3]]+=weight*correction[1]
                target[old_indices[5*leg+4]]+=weight*correction[0]
        target=np.clip(target,limits[:,0]+.015,limits[:,1]-.015)
        for _ in range(substeps):
            tau,sat,_=bank.step(d.qpos[qadr],d.qvel[vadr],target);d.ctrl[aids]=tau
            previous=d.time;mujoco.mj_step(m,d);mujoco.mj_forward(m,d)
            failure=ResidualEnv._check_physics(plant)
            if d.time<=previous:failure=failure or 'invalid_physics_time'
            failure=failure or protection.update(sat)
            heights=np.array([d.geom_xpos[g,2]-np.abs(d.geom_xmat[g].reshape(3,3)[2])@m.geom_size[g] for g in plant.soles])
            events=tracker.update(plant.loads>.35,heights,d.geom_xpos[plant.soles,:2],float(d.xpos[plant.base,0]-start[0]),d.time>=1.)
            if (protocol is not None or d.time>2.) and events['no_step_elapsed_s']>1.:failure=failure or 'walking_interrupted'
            if failure:break
        states.append(state());torques.append(tau.copy());targets.append(target.copy());actions.append(action.copy());previous_action=action.copy();i+=1
        motion.append([float(d.time),*d.xpos[plant.base,:2],float(np.arctan2(d.xmat[plant.base,3],d.xmat[plant.base,0]))])
    contacts=[{'geom1':m.geom(c.geom1).name,'geom2':m.geom(c.geom2).name,'distance_m':float(c.dist)} for c in d.contact if c.dist< -1e-8]
    a.out.mkdir(parents=True)
    np.savez_compressed(a.out/'states.npz',state=np.array(states),target=np.array(targets),last_substep_torque=np.array(torques),
                        legacy_observation=np.array(observations),legacy_action=np.array(actions),imu_observation=np.array(imu_observations),motion_xy_heading=np.array(motion),state_spec=int(STATE_SPEC))
    (a.out/'probe_source.py').write_bytes(Path(__file__).read_bytes())
    if protocol:
        (a.out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
        np.savez_compressed(a.out/'landing_events.npz',segment_counts=tracker.segment_landings,
                            events=np.array([[x['time_s'],x['segment_index'],x['foot']] for x in tracker.landing_events]).reshape(-1,3))
    report={'scope':__doc__,'design':str(a.design),'reference':str(a.reference),'requested_duration_s':a.duration,
            'formal_acceptance':False,
            'failure':failure,'time_s':float(d.time),'forward_m':float(d.xpos[plant.base,0]-start[0]),
            'yaw_change_rad':float(np.unwrap(np.array(motion)[:,3])[-1]-motion[0][3]),
            'reference_has_q12':'q12' in reference[0],
            'parameters':parameters,'randomized':a.randomize,'variation_source_sha256':sha('stackchan_rl/candidate_variation.py'),
            'valid_landings':tracker.counts.tolist(),'joint_order':names,'mass_kg':float(m.body_mass.sum()),
            'old_static_torque_mass_scale':torque_scale,'terminal_penetrating_contacts':contacts,
            'legacy_policy':str(a.policy) if a.policy else None,'legacy_policy_sha256':sha(a.policy) if a.policy else None,
            'observation_view_sha256':sha('stackchan_rl/legacy_policy_view.py') if view is not None else None,'seed':a.seed,
            'yaw_servo_gains':{'kp_Nm_rad':a.yaw_kp,'kd_Nm_s_rad':a.yaw_kd,'identified_hardware':False},
            'ankle_damping_override_Nm_s_rad':a.ankle_kd,
            'attitude_feedback':{'angle_gain':a.attitude_gain,'rate_gain_s':a.attitude_rate_gain,'axes':a.attitude_axes,'correction_limit_rad':.15,
                                 'observer':imu.metadata() if imu else None,'observer_source_sha256':sha('stackchan_rl/attitude_observer.py') if imu else None},
            'motor_parameters':{k:v.tolist() for k,v in motor.items()},
            'baseline_config_sha256':sha('policies/r6_mounted_seed20260924/config.json'),
            'peak_continuous_saturation_s':(protection.peak_streak*m.opt.timestep).tolist(),
            'peak_one_second_saturation_duty':protection.peak_duty.tolist(),
            'trajectory_sha256':sha(a.out/'states.npz'),
            'source_sha256':{str(path):sha(path) for path in [Path(__file__),a.design/'models/scene.xml',a.design/'robot.json',a.reference,
                                Path('stackchan_rl/residual.py'),Path('stackchan_rl/actuation.py'),Path('stackchan_rl/walk_events.py')]}}
    if protocol:
        measured=np.array(motion)
        scored=(score_motion(protocol,measured[:,0],measured[:,1:3],measured[:,3],allow_partial=True)
                if len(measured)>=3 else {'scope':'insufficient motion samples after immediate physics failure',
                                          'complete_schedule':False,'motion_pass':False,'segments':[]})
        landings_pass=all(s['mode']=='stop' or np.all(tracker.segment_landings[j]>=protocol['walking_evidence']['minimum_valid_landings_each_foot_per_moving_segment']) for j,s in enumerate(protocol['segments']))
        report.update(motion_scoring=scored,segment_valid_landings=tracker.segment_landings.tolist(),landing_requirements_pass=bool(landings_pass),
                      complete_schedule=scored['complete_schedule'],development_trial_pass=bool(not failure and landings_pass and scored['motion_pass']),
                      landing_events_sha256=sha(a.out/'landing_events.npz'))
        report['source_sha256'][str(a.protocol)]=sha(a.protocol)
        for path in ('stackchan_rl/maneuver_protocol.py','stackchan_rl/maneuver_env.py'):report['source_sha256'][path]=sha(path)
    report['walking_evidence']=tracker.summary()
    (a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('failure','time_s','forward_m','valid_landings','mass_kg')}))


if __name__=='__main__':main()
