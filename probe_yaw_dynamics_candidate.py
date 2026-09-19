#!/usr/bin/env python3
"""Drive a 12-axis candidate through actual constrained servo physics.

Development only: transfer the old ten-axis reference with both added yaw targets
zero. This tests the changed mass/support model, not commanded yaw capability.
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
    a=p.parse_args()
    if a.out.exists() or not np.isfinite(a.duration) or a.duration<=0:p.error('new output and positive finite duration required')
    with gzip.open(a.reference,'rt') as f:reference=json.load(f)
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
    mujoco.mj_resetDataKeyframe(m,d,0)
    d.qpos[:3]=np.array(reference[0]['base'])[:3,3];d.qpos[2]+=.0005
    initial=np.zeros(12);initial[old_indices]=reference[0]['q'];d.qpos[qadr]=initial
    mujoco.mj_forward(m,d)
    plant=SimpleNamespace(model=m,data=d,qadr=qadr,limits=limits,base=m.body('base').id,
                          floor=m.geom('floor').id,soles=np.array([m.geom('col_'+side+'_sole_TPU_0').id for side in ('left','right')]),
                          warnings=np.array([w.number for w in d.warning]),loads=np.zeros(2),force=np.zeros(6))
    bank=PostSlewLowPassBank(motor,m.opt.timestep,config['slew_rad_s'],config['lowpass_s']);bank.reset(initial)
    protection=JointProtection(m.opt.timestep,config['protection'],12)
    tracker=WalkEventTracker(m.opt.timestep,DEFAULT['env'])
    start=d.xpos[plant.base].copy();failure=ResidualEnv._check_physics(plant)
    def state():
        array=np.empty(mujoco.mj_stateSize(m,STATE_SPEC));mujoco.mj_getState(m,d,array,STATE_SPEC);return array
    states=[state()];torques=[];targets=[]
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
        if abs(sample['time_s']-i*.02)>1e-9:raise ValueError('reference sample cadence mismatch')
        target=np.zeros(12)
        target[old_indices]=np.array(sample['q'])+np.array(sample['quasistatic_torque_Nm'])*torque_scale/motor['kp'][old_indices]
        target=np.clip(target,limits[:,0]+.015,limits[:,1]-.015)
        for _ in range(substeps):
            tau,sat,_=bank.step(d.qpos[qadr],d.qvel[vadr],target);d.ctrl[aids]=tau
            previous=d.time;mujoco.mj_step(m,d);mujoco.mj_forward(m,d)
            failure=ResidualEnv._check_physics(plant)
            if d.time<=previous:failure=failure or 'invalid_physics_time'
            failure=failure or protection.update(sat)
            heights=np.array([d.geom_xpos[g,2]-np.abs(d.geom_xmat[g].reshape(3,3)[2])@m.geom_size[g] for g in plant.soles])
            events=tracker.update(plant.loads>.35,heights,d.geom_xpos[plant.soles,:2],float(d.xpos[plant.base,0]-start[0]),d.time>=1.)
            if d.time>2. and events['no_step_elapsed_s']>1.:failure=failure or 'walking_interrupted'
            if failure:break
        states.append(state());torques.append(tau.copy());targets.append(target.copy());i+=1
    contacts=[{'geom1':m.geom(c.geom1).name,'geom2':m.geom(c.geom2).name,'distance_m':float(c.dist)} for c in d.contact if c.dist< -1e-8]
    a.out.mkdir(parents=True)
    np.savez_compressed(a.out/'states.npz',state=np.array(states),target=np.array(targets),last_substep_torque=np.array(torques),state_spec=int(STATE_SPEC))
    (a.out/'probe_source.py').write_bytes(Path(__file__).read_bytes())
    report={'scope':__doc__,'design':str(a.design),'reference':str(a.reference),'requested_duration_s':a.duration,
            'failure':failure,'time_s':float(d.time),'forward_m':float(d.xpos[plant.base,0]-start[0]),
            'valid_landings':tracker.counts.tolist(),'joint_order':names,'mass_kg':float(m.body_mass.sum()),
            'old_static_torque_mass_scale':torque_scale,'terminal_penetrating_contacts':contacts,
            'peak_continuous_saturation_s':(protection.peak_streak*m.opt.timestep).tolist(),
            'peak_one_second_saturation_duty':protection.peak_duty.tolist(),
            'trajectory_sha256':sha(a.out/'states.npz'),
            'source_sha256':{str(path):sha(path) for path in [Path(__file__),a.design/'models/scene.xml',a.design/'robot.json',a.reference,
                                Path('stackchan_rl/residual.py'),Path('stackchan_rl/actuation.py'),Path('stackchan_rl/walk_events.py')]}}
    (a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('failure','time_s','forward_m','valid_landings','mass_kg')}))


if __name__=='__main__':main()
