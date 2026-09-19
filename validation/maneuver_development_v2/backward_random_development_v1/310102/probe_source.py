#!/usr/bin/env python3
"""Generate signed-speed IK targets, then measure unassisted MuJoCo response.

Development characterization only; no learned-policy or acceptance claim.
"""
import argparse
import gzip
import json
from pathlib import Path
import sys
import numpy as np
import mujoco
import scipy
from probe_reference_gait import MovingCOMReference
from stackchan_rl.residual import ResidualEnv, sha


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cad-design',type=Path,required=True)
    p.add_argument('--speed',type=float,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--steps',type=int,default=24)
    p.add_argument('--com-inset-mm',type=float,default=24.)
    p.add_argument('--com-forward-offset-mm',type=float,default=0.)
    p.add_argument('--step-period',type=float,default=.27)
    p.add_argument('--height-offset-mm',type=float,default=0.)
    p.add_argument('--step-height-mm',type=float,default=4.)
    p.add_argument('--constant-action',type=float,nargs=10,default=[0.]*10,
                   help='ten bounded residual actions; order matches config joint order')
    p.add_argument('--seed',type=int,default=310001)
    p.add_argument('--randomize',action='store_true')
    a=p.parse_args()
    if a.out.exists() or not np.isfinite(a.speed) or a.steps<4:p.error('new output, finite speed, >=4 steps required')
    if not np.isfinite(a.com_forward_offset_mm) or abs(a.com_forward_offset_mm)>15:
        p.error('COM offset must be finite and within +/-15 mm')
    if not np.isfinite(a.com_inset_mm) or not 0<=a.com_inset_mm<26:
        p.error('COM inset must be finite and within [0,26) mm')
    if not np.isfinite(a.step_period) or not .15<=a.step_period<=1.:
        p.error('step period must be in [0.15,1] seconds')
    if not np.isfinite(a.height_offset_mm) or not -10<=a.height_offset_mm<=3:
        p.error('height offset must be in [-10,3] mm')
    if not np.isfinite(a.step_height_mm) or not 2<=a.step_height_mm<=10:
        p.error('step height must be in [2,10] mm')
    action=np.asarray(a.constant_action)
    if not np.isfinite(action).all() or np.any(abs(action)>1):
        p.error('constant actions must be finite and in [-1,1]')
    if 217000<=a.seed<=217019 or 218000<=a.seed<=218019:
        p.error('acceptance seeds are reserved; this is a development probe')
    a.out.mkdir(parents=True);cad=a.cad_design.resolve()
    sys.path.insert(0,str(cad/'src'))
    from tab5_biped.core import PARAMS,smooth,SIDES
    from tab5_biped.planner import Planner,static_torques,pose
    period=a.step_period;dt=.02
    PARAMS['gait'].update(step_length_m=a.speed*period,step_height_m=a.step_height_mm/1000,initial_stand_s=1.,
                         shift_s=.35*period,swing_s=.55*period,settle_s=.1*period,com_inset_mm=a.com_inset_mm)
    initial=Planner(steps=a.steps)
    if a.height_offset_mm:
        initial.q0,initial.b0,_=pose(initial.initial_feet,initial.initial_feet.mean(axis=0)[:2],
                                    (initial.q0,initial.b0),initial.b0[2,3]+a.height_offset_mm/1000)
    planner=MovingCOMReference(initial,pose,smooth,SIDES,a.com_forward_offset_mm/1000)
    # End before the planner's terminal alignment: this probe measures walking only.
    duration=np.floor((1.+a.steps*period)/dt)*dt
    reference=[];planning_failure=None
    for t in np.arange(0,duration+dt/2,dt):
        try:
            s=planner.sample(float(t));tau,_=static_torques(s.q,s.base,s.support)
            reference.append({'time_s':float(t),'q':s.q.tolist(),'base':s.base.tolist(),
                              'support':s.support.tolist(),'quasistatic_torque_Nm':tau.tolist(),'phase':s.phase})
        except ValueError as exc:
            planning_failure={'time_s':float(t),'reason':str(exc)};break
    report={'scope':'Signed reference and unassisted development probe; not maneuver acceptance',
            'requested_vx_m_s':a.speed,'planning_failure':planning_failure,'physics_executed':False,
            'com_forward_offset_mm':a.com_forward_offset_mm,
            'step_period_s':period,'height_offset_mm':a.height_offset_mm,
            'step_height_mm':a.step_height_mm,'com_inset_mm':a.com_inset_mm,'steps':a.steps,
            'controller':'joint reference plus static torque compensation and constant residual; no learned policy',
            'constant_action':action.tolist(),'randomized':a.randomize,
            'runtime':{'python':sys.version,'numpy':np.__version__,'scipy':scipy.__version__,'mujoco':mujoco.__version__},
            'reference_generator_sha256':sha('probe_reference_gait.py'),
            'source_sha256':sha(__file__),'cad_inputs_sha256':{name:sha(cad/name) for name in ('robot.json','src/tab5_biped/core.py','src/tab5_biped/planner.py')}}
    (a.out/'probe_source.py').write_bytes(Path(__file__).read_bytes())
    (a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    if planning_failure:
        print(json.dumps(report,indent=2));return
    reference_path=a.out/'reference.json.gz'
    with gzip.open(reference_path,'wt') as f:json.dump(reference,f)
    config=json.loads(Path('policies/r6_mounted_seed20260924/config.json').read_text())
    config.update(schema='r6-residual-v1',reference=str(reference_path.resolve()),episode_s=float(duration),randomize=a.randomize)
    # Legacy constructor only accepts +0.10. Override its command-dependent
    # observations/reward explicitly after initialization; physics is unchanged.
    env=ResidualEnv(config,record=True)
    config['command_m_s']=a.speed;env.cfg['command_m_s']=a.speed
    env.fingerprint['signed_reference_probe']={'requested_vx_m_s':a.speed,'source_sha256':sha(__file__)}
    (a.out/'config.json').write_text(json.dumps(config,indent=2)+'\n')
    try:
        env.reset(seed=a.seed,options={'randomize':a.randomize})
        def current_yaw():
            rot=env.data.xmat[env.base].reshape(3,3)
            return float(np.arctan2(rot[1,0],rot[0,0]))
        yaws=[current_yaw()]
        while True:
            _,_,done,truncated,info=env.step(action)
            yaws.append(current_yaw())
            if done or truncated:break
        env.save_trajectory(a.out/'states.npz')
        states=np.asarray(env.states);late=states[:,0]>=2.
        rate=float(np.polyfit(states[late,0],states[late,1],1)[0]) if np.count_nonzero(late)>20 else None
        yaw=np.unwrap(yaws)
        yaw_rate=float(np.polyfit(states[late,0],yaw[late],1)[0]) if np.count_nonzero(late)>20 else None
        contacts=[]
        for contact in env.data.contact:
            if contact.dist<0:
                contacts.append({'geom1':env.model.geom(int(contact.geom1)).name,
                                 'geom2':env.model.geom(int(contact.geom2)).name,
                                 'distance_m':float(contact.dist)})
        report.update(physics_executed=True,seed=a.seed,**info,late_forward_speed_m_s=rate,
                      late_yaw_rate_rad_s=yaw_rate,final_yaw_change_rad=float(yaw[-1]-yaw[0]),
                      lateral_displacement_m=float(env.data.xpos[env.base,1]-env.start[1]),
                      terminal_penetrating_contacts=contacts,
                      interface=env.fingerprint,trajectory_sha256=sha(a.out/'states.npz'),
                      reference_sha256=sha(reference_path))
        (a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps({k:v for k,v in report.items() if k not in ('interface','parameters')},indent=2))
    finally:env.close()


if __name__=='__main__':main()
