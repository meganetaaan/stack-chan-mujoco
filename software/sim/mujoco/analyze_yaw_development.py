#!/usr/bin/env python3
"""Measure isolated yaw trials; deliberately cannot declare maneuver acceptance."""
import argparse,json
from pathlib import Path
import numpy as np
from stackchan_rl.residual import sha


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--trial',type=Path,required=True)
    p.add_argument('--reference-report',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    if a.out.exists():p.error('new output required')
    report=json.loads((a.trial/'report.json').read_text())
    ref=json.loads(a.reference_report.read_text())
    if report['source_sha256'][report['reference']]!=ref['reference_sha256']:raise ValueError('reference mismatch')
    if sha(a.trial/'states.npz')!=report['trajectory_sha256']:raise ValueError('trajectory mismatch')
    with np.load(a.trial/'states.npz') as z:motion=z['motion_xy_heading']
    t=motion[:,0];xy=motion[:,1:3];yaw=np.unwrap(motion[:,3]);dt=np.diff(t)
    if not np.isfinite(motion).all() or np.any(dt<=0) or np.max(dt)>.020000001:raise ValueError('invalid samples')
    protocol=json.loads(Path('configs/maneuver/acceptance_v1.json').read_text())
    # The isolated trajectory begins with one second standing before the gait.
    start=1.;stable=np.flatnonzero(t[:-1]>=start+protocol['settling_time_s']-1e-9)
    v=np.diff(xy,axis=0)/dt[:,None];h=(yaw[1:]+yaw[:-1])/2
    vx=v[:,0]*np.cos(h)+v[:,1]*np.sin(h);vy=-v[:,0]*np.sin(h)+v[:,1]*np.cos(h)
    w=np.diff(yaw)/dt;target=ref['command_yaw_rate_rad_s'];smooth=[]
    for j in stable:
        k=np.searchsorted(t,t[j+1]-protocol['velocity_smoothing_window_s'],side='left')
        smooth.append([np.average(x[k:j+1],weights=dt[k:j+1]) for x in (vx,vy,w)])
    s=np.array(smooth);avg=lambda x:float(np.average(x,weights=dt[stable]));first=np.argmin(abs(t-start))
    metrics={'mean_vx_error_m_s':abs(avg(vx[stable])), 'smoothed_vx_rmse_m_s':np.sqrt(avg(s[:,0]**2)),
             'mean_yaw_rate_error_rad_s':abs(avg(w[stable])-target),'smoothed_yaw_rate_rmse_rad_s':np.sqrt(avg((s[:,2]-target)**2)),
             'smoothed_lateral_velocity_rmse_m_s':np.sqrt(avg(s[:,1]**2)),
             'in_place_max_displacement_m':float(np.max(np.linalg.norm(xy[first:]-xy[first],axis=1)))}
    result={'scope':__doc__,'formal_acceptance':False,'complete_maneuver_schedule':False,
            'settled_interval_s':[float(t[stable[0]]),float(t[-1])], 'mean_yaw_rate_rad_s':avg(w[stable]),'metrics':metrics,
            'violations_of_corresponding_motion_thresholds':[k for k,v in metrics.items() if v>protocol['thresholds'][k]+1e-10],
            'failure':report['failure'],'valid_landings':report['valid_landings'],
            'source_sha256':{str(path):sha(path) for path in [Path(__file__),a.trial/'report.json',a.reference_report,Path('configs/maneuver/acceptance_v1.json')]}}
    a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))


if __name__=='__main__':main()
