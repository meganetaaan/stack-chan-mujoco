"""Freeze task demands from the preserved successful r9 finite-turn controller.

This is a workload source, not verification of the new actuator model.
"""
import argparse
import json
import hashlib
from pathlib import Path
import numpy as np
import mujoco
from fixtures import full_body


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',required=True,type=Path)
    a=p.parse_args()
    if a.out.exists():p.error('new workload folder required')
    a.out.mkdir(parents=True)
    requirements=[]
    for sign in [1,-1]:
        sim,names=full_body(sign,drive_model='legacy')
        matrix=np.zeros((sim.m.nv,sim.m.nv))
        mujoco.mj_fullM(sim.m,sim.d,matrix)
        inertia=np.diag(matrix)[sim.vadr]
        rows=[]
        def observe(s):
            rows.append([float(s.d.time),s.d.qpos[s.qadr].copy(),s.d.qvel[s.vadr].copy(),
                         s.d.ctrl[s.aids].copy(),s.bank.delayed.copy()])
        sim.physics_observer=observe
        for i in range(350):
            sim.step('left')
            if sim.failure:raise ValueError('legacy workload failed: '+sim.failure)
        path=a.out/('left.npz' if sign>0 else 'right.npz')
        np.savez_compressed(path,time=[r[0] for r in rows],q_rad=[r[1] for r in rows],qd_rad_s=[r[2] for r in rows],
                            torque_Nm=[r[3] for r in rows],servo_reference_rad=[r[4] for r in rows])
        q=np.array([r[1] for r in rows]);tau=np.array([r[3] for r in rows])
        if sign>0:
            for j,name in enumerate(names):
                peak=int(np.argmax(abs(tau[:,j])))
                requirements.append({'joint':name,'equivalent_inertia_kg_m2':float(inertia[j]),
                                     'required_motion_rad':[float(q[:,j].min()),float(q[:,j].max())],
                                     'external_fixture_load_Nm':float(-tau[peak,j]),
                                     'source_peak_time_s':rows[peak][0]})
    contract={'scope':__doc__,'joint_requirements':requirements,
              'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in a.out.glob('*.npz')},
              'single_joint_gates':{'steady_error_rad':.04,'transient_error_rad':.15,'settling_s':.5},
              'leg_gates':{'peak_joint_tracking_error_rad':.15,'rms_joint_tracking_error_rad':.06,
                           'no_joint_limit_violation':True,'no_self_collision':True,'no_protection_stop':True},
              'note':'Gates fixed before the new actuator fixture trials. Load is the peak legacy task torque held constant for a conservative single-joint test, not a continuous servo rating.'}
    (a.out/'requirements.json').write_text(json.dumps(contract,indent=2)+'\n')
    print(json.dumps({'joints':len(requirements),'out':str(a.out)}))


if __name__=='__main__':main()
