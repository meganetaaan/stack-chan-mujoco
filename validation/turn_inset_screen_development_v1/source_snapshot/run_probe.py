"""Development probe of the current-position model; never closes an issue alone."""
import argparse
import json
from pathlib import Path
import numpy as np
import mujoco
from fixtures import full_body
from load_export import joint_wrenches


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',required=True,type=Path)
    p.add_argument('--model', type=Path, help='Separate development model directory; defaults to frozen r9')
    p.add_argument('--turn-inset-mm', type=float, default=25.5)
    p.add_argument('--sign',type=int,choices=[-1,1],default=1)
    p.add_argument('--voltage',type=float,default=5.)
    p.add_argument('--delay',type=float,default=.010)
    p.add_argument('--backlash',type=float,default=.004363323129985824)
    a=p.parse_args()
    if a.out.exists():p.error('new output directory required')
    sim,names=full_body(a.sign,model_path=a.model,turn_inset_mm=a.turn_inset_mm,voltage=a.voltage,delay_s=a.delay,backlash=a.backlash)
    rows=[]
    def observe(s):
        t=dict(s.bank.telemetry)
        t['joint_wrench_local_force_moment']=joint_wrenches(s.m,s.d,names)
        rows.append([float(s.d.time),s.d.qpos.copy(),s.d.qvel.copy(),{k:v.copy() for k,v in t.items()}])
    sim.physics_observer=observe
    for i in range(350):
        sim.step('left')
        if sim.failure:break
    a.out.mkdir(parents=True)
    np.savez_compressed(a.out/'trace.npz',time=[r[0] for r in rows],qpos=[r[1] for r in rows],qvel=[r[2] for r in rows],
                        **{k:np.array([r[3][k] for r in rows]) for k in rows[0][3]})
    telemetry={k:np.array([r[3][k] for r in rows]) for k in rows[0][3]}
    w,x,y,z=sim.d.qpos[3:7]
    report={'failure':sim.failure,'duration_s':sim.d.time,'joint_names':names,
            'yaw_deg':float(np.rad2deg(np.arctan2(2*(w*z+x*y),1-2*(y*y+z*z)))),
            'peak_tracking_error_rad':float(np.max(abs(telemetry['tracking_error_rad']))),
            'rms_tracking_error_rad':np.sqrt(np.mean(telemetry['tracking_error_rad']**2,axis=0)).tolist(),
            'peak_current_A':np.max(abs(telemetry['motor_current_A']),axis=0).tolist(),
            'peak_total_supply_current_A':float(np.max(telemetry['supply_current_A'].sum(axis=1))),
            'peak_case_temperature_C':float(np.max(telemetry['case_temperature_C'])),
            'peak_power_balance_residual_W':float(np.max(abs(telemetry['supply_power_W']-telemetry['mechanical_power_W']-telemetry['copper_loss_W']-telemetry['gear_loss_W']-telemetry['idle_loss_W']))),
            'settings':{'model':str(a.model) if a.model else 'frozen r9','sign':a.sign,'turn_inset_mm':a.turn_inset_mm,'voltage':a.voltage,'delay_s':a.delay,'backlash_rad':a.backlash},
            'scope':'development probe, not acceptance or measured current/temperature'}
    (a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
