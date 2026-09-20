#!/usr/bin/env python3
"""Generate a twelve-axis development reference for the frozen maneuver protocol."""
import argparse,gzip,json,sys
from pathlib import Path
import numpy as np
from generate_yaw_zero_reference import configure_candidate_mass
from yaw_maneuver_reference import YawCommandReference
from stackchan_rl.yaw_kinematics import YawLegKinematics
from stackchan_rl.maneuver_protocol import validate,command_at
from stackchan_rl.residual import sha


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cad-design',type=Path,required=True)
    p.add_argument('--design',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--duration',type=float,default=205.)
    p.add_argument('--shift-fraction',type=float,default=.35)
    p.add_argument('--steady-inset-mm',type=float,default=25.5)
    a=p.parse_args()
    protocol_path=Path('configs/maneuver/acceptance_v1.json')
    protocol=json.loads(protocol_path.read_text());duration=validate(protocol)[-1]
    if a.out.exists() or not np.isfinite(a.duration) or not 0<a.duration<=duration or not np.isclose(a.duration/.02,round(a.duration/.02)):p.error('new output and duration on the 20 ms grid within the schedule required')
    sys.path.insert(0,str(a.cad_design.resolve()/'src'))
    from tab5_biped import core
    import tab5_biped.planner as legacy
    inertials=json.loads((a.design/'models/inertials.json').read_text());robot=json.loads((a.design/'robot.json').read_text())
    configure_candidate_mass(legacy,inertials,robot)
    initial=legacy.Planner(steps=1)
    initial.q0,initial.b0,_=legacy.pose(initial.initial_feet,initial.initial_feet.mean(axis=0)[:2],(initial.q0,initial.b0),initial.b0[2,3]+.002)
    kin=YawLegKinematics(core,robot['hip_yaw_candidate']['axis_base_m'],(-.075,.075))
    planner=YawCommandReference(initial,legacy.pose,core.smooth,protocol,kin,a.shift_fraction,a.steady_inset_mm)
    reference=[];failure=None
    for t in np.arange(0,a.duration+.01,.02):
        try:
            sample=planner.sample(float(t));tau,_=legacy.static_torques(sample.q,sample.base,sample.support)
            index,command=command_at(protocol,float(min(t,duration)))
            reference.append({'time_s':float(t),'q':sample.q.tolist(),'q12':sample.q12.tolist(),'base':sample.base.tolist(),
                              'support':sample.support.tolist(),'quasistatic_torque_Nm':tau.tolist(),'phase':sample.phase,
                              'segment_index':index,'command':command.tolist(),'virtual_heading':sample.virtual_heading})
        except ValueError as exc:
            failure={'time_s':float(t),'error':str(exc)};break
    a.out.mkdir(parents=True)
    with gzip.open(a.out/'reference.json.gz','wt') as f:json.dump(reference,f)
    (a.out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    sources=[Path(__file__),Path('yaw_maneuver_reference.py'),Path('maneuver_reference.py'),Path('generate_yaw_zero_reference.py'),Path('stackchan_rl/yaw_kinematics.py'),protocol_path,a.design/'models/inertials.json',a.design/'robot.json',a.cad_design/'src/tab5_biped/core.py',a.cad_design/'src/tab5_biped/planner.py']
    report={'scope':__doc__,'planning_failure':failure,'requested_duration_s':a.duration,'last_reference_time_s':reference[-1]['time_s'] if reference else None,
            'shift_fraction':a.shift_fraction,'swing_fraction':.9-a.shift_fraction,'settle_fraction':.1,
            'steady_inset_mm':a.steady_inset_mm,
            'mass_kg':legacy.MASS,'reference_sha256':sha(a.out/'reference.json.gz'),'static_compensation':'zero-yaw approximation; no yaw feedforward',
            'source_sha256':{str(path):sha(path) for path in sources}}
    (a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
    if failure:raise SystemExit(1)


if __name__=='__main__':main()
