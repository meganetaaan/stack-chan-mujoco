"""Physical one-DOF fixtures loaded with the frozen r9 task's peak torque."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np
import mujoco
from drive import CurrentPositionBank,CATALOG
from load_export import joint_wrenches

ROOT=Path(__file__).resolve().parents[3]


def trajectory(t,low,high):
    mid=(low+high)/2
    transitions=[(1.,mid,low),(2.,low,high),(3.,high,mid)]
    value=mid
    for start,a,b in transitions:
        if t<start:break
        u=np.clip((t-start)/.4,0.,1.);blend=u**3*(10-15*u+6*u*u)
        value=a+(b-a)*blend
    return value


def trial(requirement,joint,parameters,gates_config):
    kind=joint['name'].split('_',1)[1];name=joint['motor'].split()[-1]
    spec=CATALOG['models'][name];kp=6. if kind=='hip_yaw' else 3.;kd=.13 if kind=='hip_yaw' else .065
    lo,hi=joint['mechanical_range_rad'];inertia=requirement['equivalent_inertia_kg_m2']
    m=mujoco.MjModel.from_xml_string(f'''<mujoco><compiler angle="radian"/>
      <option timestep=".001" integrator="implicitfast" gravity="0 0 0"/>
      <worldbody><body name="fixture"><joint name="axis" axis="0 0 1" range="{lo} {hi}" damping=".0015" frictionloss=".006" armature=".000002"/>
      <inertial pos="0 0 0" mass=".1" diaginertia="{inertia} {inertia} {inertia}"/>
      </body></worldbody><actuator><motor joint="axis" ctrllimited="true" ctrlrange="{-spec['analysis_torque_limit_Nm']} {spec['analysis_torque_limit_Nm']}"/></actuator></mujoco>''')
    d=mujoco.MjData(m)
    motor={k:np.array([v]) for k,v in {'cap':spec['analysis_torque_limit_Nm'],'stall':spec['stall_torque_Nm'][1],
                                     'omega':spec['no_load_speed_rpm'][1]*np.pi/30,'kp':kp,'kd':kd,'delay_s':.01}.items()}
    bank=CurrentPositionBank([name],motor,**parameters)
    low,high=requirement['required_motion_rad'];mid=(low+high)/2
    load=requirement['external_fixture_load_Nm']
    d.qpos[0]=mid;bank.reset(np.array([mid]));mujoco.mj_forward(m,d)
    rows=[];failure=None;target=mid
    for i in range(5000):
        t=i*.001;desired=trajectory(t,low,high)
        # Known fixture torque is compensated through the position reference,
        # exactly as gravity compensation is added in the baseline controller.
        if i%20==0:
            # Feed forward the known commanded trajectory through the nominal
            # 40 ms target filter + 10 ms transport delay. Keep the required
            # physical trajectory and its error thresholds unchanged.
            ahead=trajectory(t+.05,low,high)
            velocity=(trajectory(t+.0501,low,high)-trajectory(t+.0499,low,high))/.0002
            target=float(np.clip(ahead-load/kp+kd*velocity/kp,lo+.015,hi-.015))
        try:
            tau,saturated,_=bank.step(d.qpos.copy(),d.qvel.copy(),np.array([target]))
        except ValueError as exc:
            failure='drive_limit: '+str(exc)
            break
        d.ctrl[:]=tau;d.qfrc_applied[0]=load
        mujoco.mj_step(m,d);mujoco.mj_forward(m,d)
        reaction=joint_wrenches(m,d,['axis'])[0]
        rows.append([float(d.time),desired,float(d.qpos[0]),float(d.qvel[0]),float(tau[0]),
                     float(bank.current[0]),float(bank.temperature[0]),*reaction])
        if not lo-1e-3<=d.qpos[0]<=hi+1e-3:failure='joint_limit';break
        if bank.temperature[0]>CATALOG['assumptions']['case_temperature_analysis_limit_C']:failure='temperature_screen';break
    data=np.array(rows);error=abs(data[:,2]-data[:,1]);steady=data[:,0]>=3.4+gates_config['settling_s']
    gates={'no_failure':failure is None,'transient_error':float(error.max())<=gates_config['transient_error_rad'],
           'steady_error':bool(steady.any() and error[steady].max()<=gates_config['steady_error_rad']),
           'current':bool(np.max(abs(data[:,5]))<=spec['analysis_current_limit_A']+1e-10)}
    return data,{'joint':joint['name'],'failure':failure,'gates':gates,'passed':all(gates.values()),
                 'max_error_rad':float(error.max()),'last_second_max_error_rad':float(error[steady].max()) if steady.any() else None,
                 'max_current_A':float(abs(data[:,5]).max()),'max_temperature_C':float(data[:,6].max()),
                 'required_load_Nm':load,'equivalent_inertia_kg_m2':inertia}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--workload',required=True,type=Path);p.add_argument('--out',required=True,type=Path)
    p.add_argument('--voltage',type=float,default=5.);p.add_argument('--delay',type=float,default=.01)
    a=p.parse_args()
    if a.out.exists():p.error('new output folder required')
    contract=json.loads((a.workload/'requirements.json').read_text())
    joints=json.loads((ROOT/'board/mechanical/prototype/joints.json').read_text())
    a.out.mkdir(parents=True);reports=[]
    for requirement,joint in zip(contract['joint_requirements'],joints):
        assert requirement['joint']==joint['name']
        data,report=trial(requirement,joint,{'voltage':a.voltage,'delay_s':a.delay},contract['single_joint_gates'])
        np.savez_compressed(a.out/(joint['name']+'.npz'),trace=data)
        reports.append(report);print(json.dumps(report),flush=True)
    summary={'scope':__doc__,'passed':all(r['passed'] for r in reports),'rows':reports,
             'columns':['time_s','desired_rad','q_rad','qd_rad_s','torque_Nm','current_A','case_temperature_C','Fx_N','Fy_N','Fz_N','Mx_Nm','My_Nm','Mz_Nm'],
             'limitations':['lumped equivalent single-axis fixtures, not full leg geometry','thermal/current values are model predictions'],
             'parameters':{'voltage':a.voltage,'delay_s':a.delay}}
    (a.out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    raise SystemExit(0 if summary['passed'] else 1)


if __name__=='__main__':main()
