"""Capture the existing r9 forward/backward maneuvers as additional leg demands."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from fixtures import SIM
from teleop_yaw import Simulation


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    if a.out.exists():p.error('new output required')
    a.out.mkdir(parents=True)
    reports=[]
    for direction in ['forward','backward']:
        model=SIM/'assets/r9_fast_turn_v1';s=Simulation(model/'reference',model,fast_turn=True);rows=[]
        def observe(sim):rows.append([float(sim.d.time),sim.d.qpos[sim.qadr].copy(),sim.d.qvel[sim.vadr].copy(),sim.d.ctrl[sim.aids].copy(),sim.bank.delayed.copy()])
        s.physics_observer=observe
        for i in range(350):
            s.step(direction if i<240 else 'stop')
            if s.failure:raise ValueError(direction+': '+s.failure)
        path=a.out/(direction+'.npz')
        np.savez_compressed(path,time=[r[0] for r in rows],q_rad=[r[1] for r in rows],qd_rad_s=[r[2] for r in rows],torque_Nm=[r[3] for r in rows],servo_reference_rad=[r[4] for r in rows])
        reports.append({'direction':direction,'failure':s.failure,'duration_s':s.d.time,'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    (a.out/'report.json').write_text(json.dumps({'scope':__doc__,'rows':reports,'note':'Current r9 commands 0.04/-0.02 m/s; not the final 0.10 m/s requirement.'},indent=2)+'\n')


if __name__=='__main__':main()
