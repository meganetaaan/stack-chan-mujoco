#!/usr/bin/env python3
"""Recompute straight gait COM/torques for the 12-axis candidate at zero yaw.

The two yaw links are lumped into the base ONLY in the reference calculation at
q_yaw=0. The actual simulator keeps all twelve joints floating and actuated.
"""
import argparse
import gzip
import json
from pathlib import Path
import sys
import numpy as np
from probe_reference_gait import MovingCOMReference
from stackchan_rl.residual import sha


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cad-design',type=Path,required=True)
    p.add_argument('--design',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--speed',type=float,default=.1)
    p.add_argument('--period',type=float,default=.27)
    p.add_argument('--step-height-mm',type=float,default=4.)
    p.add_argument('--steps',type=int,default=24)
    p.add_argument('--height-offset-mm',type=float,default=0.)
    a=p.parse_args()
    if a.out.exists() or not np.isfinite([a.speed,a.period,a.step_height_mm,a.height_offset_mm]).all() or not .15<=a.period<=1 or not 2<=a.step_height_mm<=10 or not -5<=a.height_offset_mm<=3 or a.steps<4:
        p.error('new output and finite bounded gait parameters required')
    sys.path.insert(0,str(a.cad_design.resolve()/'src'))
    from tab5_biped.core import PARAMS,SIDES,smooth
    import tab5_biped.planner as legacy
    inertials=json.loads((a.design/'models/inertials.json').read_text())
    robot=json.loads((a.design/'robot.json').read_text())
    merged=[]
    for name in ('base','left_hip_yaw','right_hip_yaw'):
        item=inertials[name];center=np.array(item['com_m'])
        if name!='base':center+=robot['hip_yaw_candidate']['axis_base_m'][name.split('_')[0]]
        merged.append((item['mass_kg'],center,np.array(item['inertia_kg_m2'])))
    mass=sum(m for m,c,I in merged);center=sum(m*c for m,c,I in merged)/mass
    inertia=sum(I+m*((c-center)@(c-center)*np.eye(3)-np.outer(c-center,c-center)) for m,c,I in merged)
    legacy.INERTIALS['base']={'mass_kg':mass,'com_m':center.tolist(),'inertia_kg_m2':inertia.tolist()}
    legacy.MASS=sum(x['mass_kg'] for x in legacy.INERTIALS.values())
    if abs(legacy.MASS-sum(x['mass_kg'] for x in inertials.values()))>1e-10:raise ValueError('mass lost while merging reference links')
    PARAMS['gait'].update(step_length_m=a.speed*a.period,step_height_m=a.step_height_mm/1000,initial_stand_s=1.,
                         shift_s=.35*a.period,swing_s=.55*a.period,settle_s=.1*a.period,com_inset_mm=24.)
    initial=legacy.Planner(steps=a.steps)
    if a.height_offset_mm:
        initial.q0,initial.b0,_=legacy.pose(initial.initial_feet,initial.initial_feet.mean(axis=0)[:2],
                                         (initial.q0,initial.b0),initial.b0[2,3]+a.height_offset_mm/1000)
    planner=MovingCOMReference(initial,legacy.pose,smooth,SIDES)
    duration=np.floor((1+a.steps*a.period)/.02)*.02
    reference=[]
    for t in np.arange(0,duration+.01,.02):
        sample=planner.sample(float(t));tau,_=legacy.static_torques(sample.q,sample.base,sample.support)
        reference.append({'time_s':float(t),'q':sample.q.tolist(),'base':sample.base.tolist(),
                          'support':sample.support.tolist(),'quasistatic_torque_Nm':tau.tolist(),'phase':sample.phase})
    a.out.mkdir(parents=True)
    with gzip.open(a.out/'reference.json.gz','wt') as f:json.dump(reference,f)
    report={'scope':__doc__,'mass_kg':legacy.MASS,'equivalent_base_at_zero_yaw':legacy.INERTIALS['base'],
            'speed_m_s':a.speed,'period_s':a.period,'step_height_mm':a.step_height_mm,'steps':a.steps,
            'height_offset_mm':a.height_offset_mm,
            'duration_s':float(duration),'reference_sha256':sha(a.out/'reference.json.gz'),
            'source_sha256':{str(path):sha(path) for path in [Path(__file__),a.design/'models/inertials.json',a.design/'robot.json',
                               a.cad_design/'src/tab5_biped/core.py',a.cad_design/'src/tab5_biped/planner.py',Path('probe_reference_gait.py')]}}
    (a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'mass_kg':legacy.MASS,'duration_s':duration}))


if __name__=='__main__':main()
