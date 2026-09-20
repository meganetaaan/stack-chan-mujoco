#!/usr/bin/env python3
"""Headless regression of Shift-WASD translation, heading hold and mode changes."""
import argparse,json,hashlib
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import numpy as np
from teleop_yaw import ROOT,Simulation


def trial(job):
    name,segments,out=job
    sim=Simulation(ROOT/'assets/r9_fast_turn_v1/reference',ROOT/'assets/r9_fast_turn_v1',fast_turn=True)
    rows=[];qposes=[]
    for seconds,command in segments:
        for _ in range(round(seconds/.02)):
            sim.step(command)
            R=sim.d.xmat[sim.plant.base].reshape(3,3)
            yaw=np.arctan2(R[1,0],R[0,0]);error=0 if sim.crab_heading is None else np.arctan2(np.sin(yaw-sim.crab_heading),np.cos(yaw-sim.crab_heading))
            rows.append([sim.d.time,sim.velocity.measured[0],sim.velocity.lateral,sim.velocity.measured[1],error,sim.lateral_control.target])
            qposes.append(sim.d.qpos.copy())
            if sim.failure:break
        if sim.failure:break
    rows=np.array(rows)
    steady=rows[(rows[:,0]>=5)&(rows[:,0]<sum(x[0] for x in segments[:-1]))]
    max_heading=float(np.rad2deg(abs(rows[:,4]).max()))
    stopped=(np.linalg.norm(rows[-1,1:3])<.004 and abs(rows[-1,3])<np.deg2rad(3) and sim.reference.mode=='stand')
    expected=np.array(segments[1][1][:2]);mean=steady[:,1:3].mean(axis=0) if len(steady) else np.zeros(2)
    passed=sim.failure is None and stopped and max_heading<5
    if len(segments)==3:passed=passed and np.all(abs(mean-expected)<.003)
    report={'name':name,'passed':bool(passed),'failure':sim.failure,'segments':segments,'time_s':float(sim.d.time),
            'max_heading_error_deg':max_heading,'mean_velocity_xy_m_s':mean.tolist(),'final_velocity':rows[-1,1:4].tolist(),'final_mode':sim.reference.mode}
    out=Path(out);np.savez_compressed(out/(name+'.npz'),trace=rows,qpos=qposes)
    (out/(name+'.json')).write_text(json.dumps(report,indent=2)+'\n')
    return report


def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--workers',type=int,default=3);a=p.parse_args()
    if a.out.exists():p.error('new output directory required')
    a.out.mkdir(parents=True)
    jobs=[]
    for x,y in [(0,.004),(0,-.004),(.015,0),(-.008,0),(.015,.004),(.015,-.004),(-.008,.004),(-.008,-.004)]:
        jobs.append((f'crab_{x}_{y}',[(2,(0,0,0)),(9,(x,y,0)),(3,(0,0,0))],str(a.out)))
    jobs.append(('long_side',[(2,(0,0,0)),(30,(0,.004,0)),(3,(0,0,0))],str(a.out)))
    jobs.append(('mode_switch',[(2,(0,0)),(2,(0,.4)),(3,(.015,.004,0)),(2,(.025,-.2)),(3,(-.008,-.004,0)),(.14,(0,0,0)),(.22,(0,.004,0)),(.18,(0,-.004,0)),(4,(0,0))],str(a.out)))
    sources=['crab_control.py','live_fast_turn_reference.py','teleop_yaw.py','velocity_control.py','run_crab_evaluation.py']
    hashes={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest() for s in sources}
    with ProcessPoolExecutor(max_workers=a.workers) as pool:
        results=list(pool.map(trial,jobs))
    summary={'passed':all(r['passed'] for r in results),'passed_count':sum(r['passed'] for r in results),'total':len(results),'results':results,'source_sha256':hashes,'source_unchanged':all(hashlib.sha256((ROOT/s).read_bytes()).hexdigest()==h for s,h in hashes.items()),'trace_columns':['time_s','vx','vy','yaw_rate','heading_error_rad','target_vy'],'limits':'Nominal MuJoCo smoke evaluation only; heading <5 deg, mean x/y error <0.003 m/s on constant commands, final stand and <0.004 m/s planar speed, <3 deg/s yaw.'}
    (a.out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary),flush=True)
    if not summary['passed']:raise SystemExit(1)


if __name__=='__main__':main()
