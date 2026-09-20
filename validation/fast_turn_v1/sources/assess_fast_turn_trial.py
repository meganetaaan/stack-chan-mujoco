#!/usr/bin/env python3
"""Development assessment: 90 +/-1 deg, yaw speed <=5 deg/s, tilt <=10 deg.

Completion is the onset of a stable stop lasting through the rest of the trial
(at least one second). Its onset must be less than three seconds after command.
Uses saved 20 ms states; time resolution is 20 ms, not hardware evidence.
"""
import argparse
import json
from pathlib import Path
import numpy as np


def assess(folder):
    report=json.loads((folder/'report.json').read_text())
    with np.load(folder/'states.npz',allow_pickle=False) as s:
        time=s['time'];q=s['qpos'];loads=s['loads'];angle=s['yaw_deg']
    if len(time)<3 or np.any(np.diff(time)<=0) or not all(np.isfinite(x).all() for x in [time,q,loads,angle]):
        raise ValueError('finite chronological states required')
    if q.shape!=(len(time),19) or loads.shape!=(len(time),2) or time[-1]<3:
        raise ValueError('complete r9 state array and at least one command second required')
    if not np.allclose(np.linalg.norm(q[:,3:7],axis=1),1,atol=1e-7):
        raise ValueError('unit base quaternions required')
    w,x,y,z=q[:,3:7].T
    measured=np.arctan2(2*(w*z+x*y),1-2*(y*y+z*z))
    origin=np.flatnonzero(time>=2)[0]
    derived=np.rad2deg(np.arctan2(np.sin(measured-measured[origin]),np.cos(measured-measured[origin])))
    if not np.allclose(derived[origin:],angle[origin:],atol=1e-7):
        raise ValueError('reported yaw disagrees with recorded body orientation')
    angle=derived
    target=90*np.sign(report['settings']['rate_deg_s'])
    error=(angle-target+180)%360-180
    rate=np.gradient(np.rad2deg(np.unwrap(np.deg2rad(angle))),time)
    tilt=np.rad2deg(np.arccos(np.clip(1-2*(q[:,4]**2+q[:,5]**2),-1,1)))
    good=(time>=2)&(abs(error)<=1)&(abs(rate)<=5)&(tilt<=10)&np.all(loads>.35,axis=1)
    through_end=np.logical_and.accumulate(good[::-1])[::-1]
    candidates=np.flatnonzero(through_end & (time<=time[-1]-1))
    onset=None if not len(candidates) else float(time[candidates[0]]-2)
    events=report.get('landing_events',[])
    step_count=None if onset is None else sum(2<=t<=2+onset for t,foot in events)
    return {'scope':__doc__,'trial':str(folder),'failure':report['failure'],
            'stable_stop_onset_s':onset,'qualified_landings_at_stop':step_count,
            'final_error_deg':float(error[-1]),'max_tilt_deg':float(tilt.max()),
            'nominal_development_pass':bool(report['failure'] is None and onset is not None and onset<3),
            'limitations':['nominal trial only','20 ms state sampling','not a complete CAD or robustness audit']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--trial',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    if a.out.exists():p.error('new output required')
    r=assess(a.trial);a.out.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
