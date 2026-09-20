"""Publish one time-aligned load bundle for circuit and structural consumers."""
import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path
import numpy as np
from load_export import circuit_load,structural_load


def export(source,out):
    if out.exists():raise ValueError('new output required')
    out.mkdir(parents=True)
    report=json.loads((source/'report.json').read_text());names=report['joint_names']
    with np.load(source/'trace.npz') as original:trace={k:original[k] for k in original.files}
    time=trace['time'];dt=np.median(np.diff(time))
    if not np.allclose(np.diff(time),.001,atol=1e-8):raise ValueError('1 ms source required')
    forces=structural_load(trace);bus=circuit_load(trace)
    velocity=trace.get('qd_rad_s',trace.get('angular_velocity_rad_s'))
    acceleration=np.gradient(velocity,time,axis=0)
    active=(abs(trace['motor_current_A'])>=.05).sum(axis=1)
    np.savez_compressed(out/'loads.npz',time_s=time,joint_wrench_local_force_moment=forces,
                        motor_current_A=trace['motor_current_A'],torque_Nm=trace['torque_Nm'],
                        supply_current_A=trace['supply_current_A'],copper_loss_W=trace['copper_loss_W'],
                        gear_loss_W=trace['gear_loss_W'],idle_loss_W=trace['idle_loss_W'],
                        mechanical_power_W=trace['mechanical_power_W'],supply_power_W=trace['supply_power_W'],
                        joint_velocity_rad_s=velocity,joint_acceleration_rad_s2=acceleration,
                        active_axis_count=active,simultaneous_drive_fraction=active/len(names),**bus)
    with gzip.open(out/'bus.csv.gz','wt',newline='') as f:
        w=csv.writer(f,lineterminator='\n');w.writerow(['time_s','draw_A','regeneration_A','net_A','active_axis_count'])
        w.writerows(zip(time,bus['draw_A'],bus['regeneration_A'],bus['net_A'],active))
    with gzip.open(out/'joints.csv.gz','wt',newline='') as f:
        w=csv.writer(f,lineterminator='\n');w.writerow(['time_s','joint','Fx_N','Fy_N','Fz_N','Mx_Nm','My_Nm','Mz_Nm','motor_current_A','shaft_torque_Nm','joint_velocity_rad_s','joint_acceleration_rad_s2'])
        for i,t in enumerate(time):
            for j,name in enumerate(names):w.writerow([t,name,*forces[i,j],trace['motor_current_A'][i,j],trace['torque_Nm'][i,j],velocity[i,j],acceleration[i,j]])
    selected=[]
    for j,name in enumerate(names):
        for kind,values in [('force_norm_N',np.linalg.norm(forces[:,j,:3],axis=1)),('moment_norm_Nm',np.linalg.norm(forces[:,j,3:],axis=1)),('absolute_acceleration_rad_s2',abs(acceleration[:,j]))]:
            i=int(np.argmax(values));selected.append({'criterion':name+':'+kind,'index':i,'time_s':float(time[i]),'value':float(values[i]),
                'simultaneous_joint_wrenches':forces[i].tolist(),'simultaneous_motor_currents_A':trace['motor_current_A'][i].tolist()})
    metadata={'schema_version':1,'scope':__doc__,'joint_names':names,'sample_period_s':float(dt),
              'wrench_order':['Fx_N','Fy_N','Fz_N','Mx_Nm','My_Nm','Mz_Nm'],
              'wrench_frame':'joint body local axes at joint origin; parent-on-child total interface wrench',
              'wrench_method':'mj_rnePostConstraint cfrc_int; shift from subtree COM then rotate world to joint-body coordinates',
              'actuation_time':'current/power use state at start of interval; force/state stored at interval end (1 ms later)',
              'current_scope':'motor_current is motor-side; supply_current is ideal bridge DC-side including standby',
              'active_axis_threshold_motor_current_A':.05,
              'acceleration_method':'finite difference of stored angular velocity; first-order endpoints',
              'source_trace_sha256':hashlib.sha256((source/'trace.npz').read_bytes()).hexdigest(),
              'source_report':report,'selected_simultaneous_cases':selected,
              'peak_draw_A':float(bus['draw_A'].max()),'peak_regeneration_A':float(bus['regeneration_A'].max()),
              'limitations':['not measured hardware loads','load cases are simultaneous samples, not independent maxima combined',
                             'power stage absorption of regeneration is not yet designed','interface resultant excludes internal gearbox tooth/shaft bearing distribution']}
    (out/'schema.json').write_text(json.dumps(metadata,indent=2)+'\n')
    return metadata


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();r=export(a.source,a.out);print(json.dumps({'joints':len(r['joint_names']),'peak_draw_A':r['peak_draw_A']}))
