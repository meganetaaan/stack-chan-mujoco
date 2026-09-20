#!/usr/bin/env python3
"""Reproducible r9 velocity tracking grid, transitions and plant perturbations."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
from pathlib import Path
import numpy as np
import mujoco
from teleop_yaw import ROOT,Simulation


def run_case(job):
    name,segments,feedback,mass,friction,out=job
    model=ROOT/'assets/r9_fast_turn_v1'
    sim=Simulation(model/'reference',model,fast_turn=True)
    sim.velocity.feedback=feedback
    if mass!=1 or friction!=.8:
        q=sim.d.qpos.copy();v=sim.d.qvel.copy()
        sim.m.body_mass[:]*=mass;sim.m.body_inertia[:]*=mass
        sim.m.geom_friction[:,0]=friction
        mujoco.mj_setConst(sim.m,sim.d)
        sim.d.qpos[:]=q;sim.d.qvel[:]=v;mujoco.mj_forward(sim.m,sim.d)
    rows=[];positions=[];tilts=[];segment_ids=[];max_torque=0.;max_penetration=0.
    for segment_id,(duration,v,w) in enumerate(segments):
        for _ in range(round(duration/.02)):
            sim.step(np.array([v,np.deg2rad(w)]))
            ctl=sim.velocity
            R=sim.d.xmat[sim.plant.base].reshape(3,3)
            tilts.append(float(np.rad2deg(np.arccos(np.clip(R[2,2],-1,1)))))
            rows.append([sim.d.time,*ctl.request,*ctl.target,*ctl.measured,ctl.lateral,*ctl.drive])
            positions.append(sim.d.qpos.copy());segment_ids.append(segment_id)
            max_torque=max(max_torque,float(np.max(abs(sim.d.ctrl[sim.aids])/sim.motor['cap'])))
            for c in sim.d.contact:
                if sim.plant.floor not in (c.geom1,c.geom2):max_penetration=max(max_penetration,float(-c.dist))
            if sim.failure:break
        if sim.failure:break
    rows=np.array(rows);positions=np.array(positions);ids=np.array(segment_ids)
    samples=rows[(rows[:,0]>=5)&(rows[:,0]<10)] if len(segments)==3 else np.empty((0,11))
    metrics={}
    if len(samples):
        error=samples[:,5:7]-samples[:,3:5]
        metrics={'target_mean':samples[:,3:5].mean(axis=0).tolist(),
                 'measured_mean':samples[:,5:7].mean(axis=0).tolist(),
                 'mean_error':error.mean(axis=0).tolist(),'rmse':np.sqrt((error**2).mean(axis=0)).tolist(),
                 'lateral_rms_m_s':float(np.sqrt((samples[:,7]**2).mean()))}
    final=rows[-1,5:7]
    stop_start=sum(x[0] for x in segments[:-1]);settling=None
    stopped=(abs(rows[:,5])<.004)&(abs(rows[:,6])<np.deg2rad(3))&(ids==len(segments)-1)
    for i in np.flatnonzero(stopped):
        if rows[-1,0]-rows[i,0]>=.5 and stopped[i:].all():settling=float(rows[i,0]-stop_start);break
    passed=(sim.failure is None and sim.reference.mode=='stand' and settling is not None and settling<2.5)
    if metrics:
        passed=passed and all(abs(np.array(metrics['mean_error']))<np.array([.004,np.deg2rad(3)]))
        passed=passed and all(np.array(metrics['rmse'])<np.array([.008,np.deg2rad(5)])) and metrics['lateral_rms_m_s']<.012
    report={'name':name,'passed':bool(passed),'failure':sim.failure,'segments':segments,'feedback':feedback,
            'mass_scale':mass,'friction':friction,'simulation_s':float(sim.d.time),'metrics':metrics,
            'stop_settling_s':settling,'final_velocity':final.tolist(),'max_tilt_deg':max(tilts),
            'max_torque_cap_fraction':max_torque,'max_nonfloor_penetration_m_20ms_samples':max_penetration,
            'final_mode':sim.reference.mode}
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(out/(name+'.npz'),trace=rows,qpos=positions,segment=ids,tilt_deg=tilts)
    (out/(name+'.json')).write_text(json.dumps(report,indent=2)+'\n')
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,required=True);p.add_argument('--workers',type=int,default=3)
    p.add_argument('--quick',action='store_true')
    a=p.parse_args()
    if a.out.exists():p.error('use a new output directory')
    a.out.mkdir(parents=True)
    jobs=[]
    speeds=[-.012,0,.025];turns=[-32,-12,0,12,32] if not a.quick else [-12,12]
    for v in speeds:
        for w in turns:
            jobs.append((f'grid_{v}_{w}',[(2,0,0),(9,v,w),(3,0,0)],True,1.,.8,str(a.out)))
    curves=[(.025,12),(.025,-12),(-.012,12),(-.012,-12)]
    if not a.quick:
        for v,w in curves:
            jobs.append((f'open_{v}_{w}',[(2,0,0),(9,v,w),(3,0,0)],False,1.,.8,str(a.out)))
            for mass,friction in [(.95,.8),(1.05,.8),(1.,.7),(1.,.9)]:
                jobs.append((f'perturb_{v}_{w}_{mass}_{friction}',[(2,0,0),(9,v,w),(3,0,0)],True,mass,friction,str(a.out)))
    seq=[(2,0,0),(2.14,.025,32),(2.18,-.012,-32),(2.26,.025,-32),(2.12,-.012,32),
         (1.14,0,32),(.14,0,0),(.18,.025,-32),(.22,-.012,32),(3,0,0)]
    jobs.append(('reversals',seq,True,1.,.8,str(a.out)))
    sources=[ROOT/x for x in ['teleop_yaw.py','velocity_control.py','live_fast_turn_reference.py','fast_turn_reference.py','run_velocity_evaluation.py','assets/r9_fast_turn_v1/models/scene.xml']]
    hashes={str(x.relative_to(ROOT)):hashlib.sha256(x.read_bytes()).hexdigest() for x in sources}
    results=[]
    with ProcessPoolExecutor(max_workers=a.workers) as pool:
        for r in pool.map(run_case,jobs):
            results.append(r);print(json.dumps(r),flush=True)
    required=[r for r in results if r['feedback']]
    summary={'passed':all(r['passed'] for r in required),'passed_required':sum(r['passed'] for r in required),
             'total_required':len(required),'results':results,'source_sha256':hashes,
             'source_unchanged':all(hashlib.sha256((ROOT/x).read_bytes()).hexdigest()==h for x,h in hashes.items()),
             'criteria':{'mean_error':[.004,float(np.deg2rad(3))],'rmse':[.008,float(np.deg2rad(5))],
                         'lateral_rms_m_s':.012,'stop_settling_s':2.5},
             'trace_columns':['time','request_v','request_w','target_v','target_w','measured_v','measured_w','lateral_v','drive_v','drive_w'],
             'limitations':['MuJoCo only; no hardware velocity estimator validated','finite grid, not proof of all possible inputs',
                            'transition case scored for safety and final stopping; steady speed error scored on grid/perturbation cases']}
    (a.out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k not in ('results','source_sha256')}))
    if not summary['passed']:raise SystemExit(1)


if __name__=='__main__':main()
