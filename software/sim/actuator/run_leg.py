"""Single-leg CAD fixtures: half-body vertical support and mounted swing/yaw.

The support bench constrains horizontal translation and attitude, but cannot
support vertical weight. The swing bench fixes the torso and removes the floor.
These are explicit test fixtures, not assisted full-body walking claims.
"""
import argparse
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
import numpy as np
import mujoco
from drive import CurrentPositionBank,CATALOG,SIM
from fixtures import full_body
from load_export import joint_wrenches,circuit_load
from stackchan_rl.residual import runtime_xml
from probe_yaw_dynamics_candidate import JointProtection

ROOT=Path(__file__).resolve().parents[3]


def fixture(side,mode,mass_scale=1.,friction_scale=1.):
    full,names=full_body(1,drive_model='legacy')
    tree=ET.fromstring(runtime_xml(SIM/'assets/r9_fast_turn_v1/models/scene.xml',visuals=False))
    base=tree.find('.//body[@name="base"]');other='right' if side=='left' else 'left'
    base.remove(base.find('body[@name="'+other+'_hip_yaw"]'))
    for joint in list(base.findall('freejoint'))+list(base.findall('joint')):base.remove(joint)
    if mode!='swing':ET.SubElement(base,'joint',name='fixture_vertical',type='slide',axis='0 0 1',limited='false')
    base.set('pos',' '.join(map(str,full.d.qpos[:3])))
    inertia=base.find('inertial');inertia.set('mass',str(float(inertia.get('mass'))*.5))
    for key in ['fullinertia','diaginertia']:
        if key in inertia.attrib:inertia.set(key,' '.join(str(float(x)*.5) for x in inertia.get(key).split()))
    for item in list(tree.find('actuator')):
        if not item.get('joint','').startswith(side+'_'):tree.find('actuator').remove(item)
    sensors=tree.find('sensor')
    if sensors is not None:
        for sensor in list(sensors):
            if any(sensor.get(key,'').startswith(other+'_') for key in ['name','joint','objname','site']):sensors.remove(sensor)
    keyframe=tree.find('keyframe')
    if keyframe is not None:tree.remove(keyframe)
    if mode=='swing':
        floor=tree.find('.//geom[@name="floor"]');floor.set('contype','0');floor.set('conaffinity','0')
    model=mujoco.MjModel.from_xml_string(ET.tostring(tree,encoding='unicode'))
    model.body_mass[:]*=mass_scale;model.body_inertia[:]*=mass_scale
    model.dof_frictionloss[:]*=friction_scale
    data=mujoco.MjData(model);mujoco.mj_setConst(model,data)
    selected=[i for i,n in enumerate(names) if n.startswith(side+'_')]
    names=[names[i] for i in selected]
    motor={k:v[selected] for k,v in full.motor.items()}
    return model,data,names,motor,selected


def run(workload,out,side,mode,parameters,mass_scale=1.,friction_scale=1.,trajectory_file='left.npz'):
    contract=json.loads((workload/'requirements.json').read_text())
    if Path(trajectory_file).name!=trajectory_file:raise ValueError('trajectory must name a workload file')
    with np.load(workload/trajectory_file) as source:
        times=source['time'];desired_all=source['q_rad'];servo_all=source['servo_reference_rad']
    m,d,names,motor,indices=fixture(side,mode,mass_scale,friction_scale)
    qadr=np.array([m.joint(n).qposadr[0] for n in names]);vadr=np.array([m.joint(n).dofadr[0] for n in names])
    aids=np.array([m.actuator(n+'_motor').id for n in names]);limits=np.array([m.joint(n).range for n in names])
    models=['XC330-M288-T' if n.split('_',1)[1] in ['hip_roll','knee','ankle_pitch'] else 'XL330-M288-T' for n in names]
    bank=CurrentPositionBank(models,motor,**parameters)
    index=int(np.searchsorted(times,1.8)) if mode!='swing' else 0
    d.qpos[qadr]=desired_all[index,indices];mujoco.mj_forward(m,d);bank.reset(d.qpos[qadr])
    target=d.qpos[qadr].copy();ref=mujoco.MjData(m)
    cfg=json.loads((SIM/'policies/r6_mounted_seed20260924/config.json').read_text())['protection']
    protection=JointProtection(.001,cfg,6)
    rows=[];failure=None;floor=m.geom('floor').id;cf=np.zeros(6)
    for tick in range(7000):
        t=tick*.001
        desired=desired_all[index,indices] if mode!='swing' else np.array([np.interp(t,times,desired_all[:,i]) for i in indices])
        if tick%20==0:
            if mode!='swing':target=servo_all[index,indices].copy()
            else:
                ahead=np.array([np.interp(t+.05,times,desired_all[:,i]) for i in indices])
                velocity=np.array([(np.interp(t+.051,times,desired_all[:,i])-np.interp(t+.049,times,desired_all[:,i]))/.002 for i in indices])
                ref.qpos[qadr]=ahead;ref.qvel[:]=0;mujoco.mj_forward(m,ref)
                target=ahead+(ref.qfrc_bias[vadr]+motor['kd']*velocity)/motor['kp']
            target=np.clip(target,limits[:,0]+.015,limits[:,1]-.015)
        tau,sat,_=bank.step(d.qpos[qadr],d.qvel[vadr],target)
        load_fraction=1.
        if mode=='transfer':
            if 2<=t<3:load_fraction=1-.5*(t-2)
            elif 3<=t<4:load_fraction=.5
            elif 4<=t<5:load_fraction=.5+.5*(t-4)
            d.xfrc_applied[m.body('base').id,2]=(1-load_fraction)*m.body_mass.sum()*9.81
        d.ctrl[aids]=tau;mujoco.mj_step(m,d);mujoco.mj_forward(m,d)
        floor_load=0.
        for contact_index,c in enumerate(d.contact):
            if floor in [c.geom1,c.geom2]:
                mujoco.mj_contactForce(m,d,contact_index,cf)
                world=c.frame.reshape(3,3).T@cf[:3]
                floor_load+=world[2]*(1 if c.geom1==floor else -1)
            elif c.dist<-.0001:failure='self_collision'
        if np.any(d.qpos[qadr]<limits[:,0]-.001) or np.any(d.qpos[qadr]>limits[:,1]+.001):failure='joint_limit'
        failure=failure or protection.update(sat)
        if not np.isfinite(d.qpos).all():failure='nonfinite'
        if np.max(bank.temperature)>CATALOG['assumptions']['case_temperature_analysis_limit_C']:failure='temperature_screen'
        state={'time':float(d.time),'desired_rad':desired.copy(),'q_rad':d.qpos[qadr].copy(),
               'qd_rad_s':d.qvel[vadr].copy(),'floor_load_N':floor_load,'expected_floor_load_N':load_fraction*m.body_mass.sum()*9.81,'base_z_m':float(d.xpos[m.body('base').id,2]),
               'joint_wrench_local_force_moment':joint_wrenches(m,d,names),
               **{k:v.copy() for k,v in bank.telemetry.items()}}
        rows.append(state)
        if failure:break
    trace={k:np.array([r[k] for r in rows]) for k in rows[0]}
    out.mkdir(parents=True)
    np.savez_compressed(out/'trace.npz',**trace)
    error=abs(trace['q_rad']-trace['desired_rad']);g=contract['leg_gates'];steady=trace['time']>=4
    gates={'no_failure':failure is None,'duration':len(rows)==7000,
           'peak_error':float(error.max())<=g['peak_joint_tracking_error_rad'],
           'rms_error':bool(np.all(np.sqrt(np.mean(error**2,axis=0))<=g['rms_joint_tracking_error_rad']))}
    if mode=='support':gates['vertical_support']=bool(steady.any() and np.min(trace['floor_load_N'][steady])>=.9*m.body_mass.sum()*9.81)
    elif mode=='transfer':
        windows=((trace['time']>=1)&(trace['time']<=1.9))|((trace['time']>=3.4)&(trace['time']<=3.9))|(trace['time']>=6)
        gates['load_transfer']=bool(np.max(abs(trace['floor_load_N'][windows]-trace['expected_floor_load_N'][windows]))<=.15*m.body_mass.sum()*9.81)
    else:gates['fixture_has_no_floor_load']=bool(np.max(abs(trace['floor_load_N']))<1e-12)
    bus=circuit_load(trace)
    report={'scope':__doc__,'side':side,'mode':mode,'trajectory_file':trajectory_file,'joint_names':names,'failure':failure,'gates':gates,
            'passed':all(gates.values()),'max_error_rad':float(error.max()),
            'rms_error_rad':np.sqrt(np.mean(error**2,axis=0)).tolist(),
            'minimum_steady_floor_load_N':float(np.min(trace['floor_load_N'][steady])) if steady.any() else None,
            'fixture_weight_N':float(m.body_mass.sum()*9.81),
            'peak_draw_A':float(bus['draw_A'].max()),'peak_regeneration_A':float(bus['regeneration_A'].max()),
            'max_case_temperature_C':float(trace['case_temperature_C'].max()),
            'parameters':{**parameters,'mass_scale':mass_scale,'friction_scale':friction_scale},
            'limitations':['explicit laboratory fixture constraints','not free-standing one-legged balance','model-estimated electrical/thermal quantities']}
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--workload',required=True,type=Path);p.add_argument('--out',required=True,type=Path)
    p.add_argument('--side',choices=['left','right'],required=True);p.add_argument('--mode',choices=['support','swing','transfer'],required=True)
    p.add_argument('--trajectory',default='left.npz')
    p.add_argument('--voltage',type=float,default=5.);p.add_argument('--delay',type=float,default=.01)
    p.add_argument('--current-tau',type=float,default=.002);p.add_argument('--backlash',type=float,default=.004363323129985824)
    p.add_argument('--mass-scale',type=float,default=1.);p.add_argument('--friction-scale',type=float,default=1.)
    a=p.parse_args()
    if a.out.exists():p.error('new output directory required')
    report=run(a.workload,a.out,a.side,a.mode,{'voltage':a.voltage,'delay_s':a.delay,'current_tau':a.current_tau,'backlash':a.backlash},a.mass_scale,a.friction_scale,a.trajectory)
    print(json.dumps(report,indent=2));raise SystemExit(0 if report['passed'] else 1)


if __name__=='__main__':main()
