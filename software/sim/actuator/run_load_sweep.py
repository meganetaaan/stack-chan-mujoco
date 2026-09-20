"""Repeat a 0.10-rad position step under increasing constant output load."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import run_single_joint as fixture
from drive import CATALOG

ROOT=Path(__file__).resolve().parents[3]


def step_trajectory(t,low,high):
    mid=(low+high)/2
    return mid if t<1 or t>=3 else (high if t<2 else low)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--workload',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    if a.out.exists():p.error('new output required')
    a.out.mkdir(parents=True)
    contract=json.loads((a.workload/'requirements.json').read_text())
    joints=json.loads((ROOT/'board/mechanical/prototype/joints.json').read_text())
    cases=[]
    for name in ['left_hip_pitch','left_knee']:
        for voltage in [3.7,5.,6.]:
            for fraction in [0.,.25,.5,.75,1.,1.25]:cases.append({'joint':name,'voltage':voltage,'fraction_of_analysis_torque_cap':fraction})
    sources=[Path(__file__),Path(fixture.__file__),Path(__file__).with_name('drive.py'),Path(__file__).with_name('catalog.json')]
    plan={'cases':cases,'step_rad':.10,'settling_s':.5,'steady_error_rad':.04,
          'note':'Overload cases are required to fail; this sweep characterizes limits rather than requiring every load to pass.',
          'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}}
    (a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    fixture.trajectory=step_trajectory;rows=[]
    for i,case in enumerate(cases):
        joint=next(j for j in joints if j['name']==case['joint'])
        required=dict(next(r for r in contract['joint_requirements'] if r['joint']==case['joint']))
        mid=np.mean(required['required_motion_rad']);required['required_motion_rad']=[float(mid-.05),float(mid+.05)]
        required['external_fixture_load_Nm']=-case['fraction_of_analysis_torque_cap']*joint['simulation_torque_limit_Nm']
        trace,report=fixture.trial(required,joint,{'voltage':case['voltage']},contract['single_joint_gates'])
        np.savez_compressed(a.out/f'case_{i:02d}.npz',trace=trace)
        hold=trace[:,0]>=3.5
        settled=bool(hold.any() and np.max(abs(trace[hold,1]-trace[hold,2]))<=.04)
        rows.append({'case':i,**case,'report':report,'step_settled':settled,
                     'passed_load_point':report['failure'] is None and settled})
        print(json.dumps({'case':i,'motor':joint['motor'],'voltage':case['voltage'],'load_fraction':case['fraction_of_analysis_torque_cap'],'passed_load_point':rows[-1]['passed_load_point']}),flush=True)
    overload=[r for r in rows if r['fraction_of_analysis_torque_cap']>1]
    summary={'scope':__doc__,'complete':len(rows)==36,'overload_detected':all(not r['passed_load_point'] for r in overload),
             'passed_load_points':sum(r['passed_load_point'] for r in rows),'rows':rows,
             'limitations':['short tests do not establish continuous thermal ratings','same physical-unit effective controller as other fixtures']}
    (a.out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k not in ['rows','limitations']}))


if __name__=='__main__':main()
