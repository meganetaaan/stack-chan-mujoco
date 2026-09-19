#!/usr/bin/env python3
"""Development foot-heading cycle; stance counter-rotates, swing resets heading.

No base state is imposed on the simulator. This kinematic seed retains the old
static compensation as an approximation; it is not a full turning COM planner.
"""
import argparse
import gzip
import json
from pathlib import Path
import sys
import numpy as np
from stackchan_rl.yaw_kinematics import YawLegKinematics
from stackchan_rl.residual import sha


def foot_yaw(t, leg, rate, period):
    start=1.+(.35+ (1 if leg==0 else 0))*period
    swing=.55*period
    if t<=1:return 0.
    if t<start:return -rate*(t-1)
    cycle=int(np.floor((t-start)/(2*period)))
    elapsed=t-start-cycle*2*period
    high=rate*(2*period-swing)/2
    low=-rate*(start-1) if cycle==0 else -high
    if elapsed<swing:
        # Cubic Hermite interpolation has the same -rate slope as stance at both ends.
        u=elapsed/swing
        return (2*u**3-3*u*u+1)*low+(-2*u**3+3*u*u)*high-rate*swing*(2*u**3-3*u*u+u)
    return high-rate*(elapsed-swing)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cad-design',type=Path,required=True)
    p.add_argument('--design',type=Path,required=True)
    p.add_argument('--reference',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--rate',type=float,required=True)
    p.add_argument('--period',type=float,default=.32)
    a=p.parse_args()
    if a.out.exists() or not np.isfinite([a.rate,a.period]).all() or not .15<=a.period<=1:p.error('new output and finite bounded period required')
    sys.path.insert(0,str(a.cad_design.resolve()/'src'))
    from tab5_biped import core
    robot=json.loads((a.design/'robot.json').read_text())
    kin=YawLegKinematics(core,robot['hip_yaw_candidate']['axis_base_m'],(-.075,.075))
    with gzip.open(a.reference,'rt') as f:ref=json.load(f)
    max_error=0.
    for sample in ref:
        old=np.array(sample['q']);base=np.array(sample['base']);q=[]
        for leg,side in enumerate(('left','right')):
            sole=core.fk_leg(old[leg*5:leg*5+5],side,base)[1]
            heading=foot_yaw(sample['time_s'],leg,a.rate,a.period)
            solved,_,_=kin.solve_flat_foot(sole[:3,3],heading,side,base)
            actual=kin.fk_leg(solved,side,base)[1]
            max_error=max(max_error,float(np.linalg.norm(actual[:3,3]-sole[:3,3])))
            q.extend(solved.tolist())
        sample['q12']=q
    if max_error>1e-7:raise ValueError('foot position changed in heading IK')
    a.out.mkdir(parents=True)
    with gzip.open(a.out/'reference.json.gz','wt') as f:json.dump(ref,f)
    report={'scope':__doc__,'command_yaw_rate_rad_s':a.rate,'period_s':a.period,'max_foot_position_error_m':max_error,
            'static_compensation':'unchanged straight-reference approximation; no yaw feedforward',
            'reference_sha256':sha(a.out/'reference.json.gz'),
            'source_sha256':{str(path):sha(path) for path in [Path(__file__),a.reference,a.design/'robot.json',a.cad_design/'src/tab5_biped/core.py',Path('stackchan_rl/yaw_kinematics.py')]}}
    (a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'max_foot_position_error_m':max_error}))


if __name__=='__main__':main()
