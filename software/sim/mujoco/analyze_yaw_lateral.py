#!/usr/bin/env python3
"""Decompose recorded lateral RMSE into bias and oscillation without changing scoring."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np


def analyze(trial):
    report=json.loads((trial/'report.json').read_text())
    protocol=json.loads((trial/'protocol.json').read_text())
    trace=trial/'states.npz'
    if hashlib.sha256(trace.read_bytes()).hexdigest()!=report['trajectory_sha256']:
        raise ValueError('state hash mismatch')
    with np.load(trace,allow_pickle=False) as data:
        motion=data['motion_xy_heading']
        np.testing.assert_allclose(motion[:,0],data['state'][:,0],atol=1e-12,rtol=0)
    t=motion[:,0];xy=motion[:,1:3];yaw=np.unwrap(motion[:,3])
    dt=np.diff(t);velocity=np.diff(xy,axis=0)/dt[:,None]
    angle=(yaw[:-1]+yaw[1:])/2
    lateral=-velocity[:,0]*np.sin(angle)+velocity[:,1]*np.cos(angle)
    rows=[]
    for segment in report['motion_scoring']['segments']:
        start,end=segment['start_s'],segment['end_s']
        first=int(np.argmin(abs(t-start)))
        stable=np.flatnonzero((t[:-1]>=start+protocol['settling_time_s']-1e-9)&(t[1:]<=end+1e-9))
        smoothed=[];counts=[]
        for j in stable:
            k=max(first,int(np.searchsorted(t,t[j+1]-protocol['velocity_smoothing_window_s'],side='left')))
            smoothed.append(np.average(lateral[k:j+1],weights=dt[k:j+1]))
            counts.append(j+1-k)
        values=np.array(smoothed);weights=dt[stable]
        avg=lambda v:float(np.average(v,weights=weights))
        mean=avg(values);variance=avg((values-mean)**2);rmse=np.sqrt(avg(values**2))
        expected=segment['metrics']['smoothed_lateral_velocity_rmse_m_s']
        if not np.isclose(rmse,expected,rtol=1e-10,atol=1e-12):raise ValueError('diagnostic differs from frozen scorer')
        rows.append({'name':segment['name'],'mean_lateral_m_s':mean,
                     'oscillation_std_m_s':float(np.sqrt(variance)),
                     'rmse_m_s':float(rmse),'bias_fraction_of_squared_rmse':mean**2/max(rmse**2,1e-30),
                     'raw_lateral_std_m_s':float(np.sqrt(avg((lateral[stable]-avg(lateral[stable]))**2))),
                     'smoothing_sample_counts':sorted(set(map(int,counts))),
                     'violations':segment['violations']})
    return {'scope':__doc__,'trial':str(trial),'segments':rows,
            'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in
                             [Path(__file__),trial/'report.json',trial/'protocol.json',trace]}}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--trial',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    if args.out.exists():parser.error('new output required')
    result=analyze(args.trial)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps([s for s in result['segments'] if s['violations']]))
