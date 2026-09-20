"""Command schedule and measured-motion scoring, separate from physics safety.

Passing this module alone is never an accepted robot trial. The runner must also
check contacts, falls, limits, actuator protection and uninterrupted execution.
"""
import math
import numpy as np


def validate(protocol):
    if protocol['schema'] != 'tab5-maneuver-protocol-v1':
        raise ValueError('unsupported maneuver protocol')
    segments=protocol['segments'];names=[s['name'] for s in segments]
    if not segments or len(names)!=len(set(names)):raise ValueError('unique segment names required')
    settling=protocol['settling_time_s'];window=protocol['velocity_smoothing_window_s']
    if not 0<window<=settling:raise ValueError('invalid settling/smoothing interval')
    for s in segments:
        if not np.isfinite([s['duration_s'],s['vx_m_s'],s['yaw_rate_rad_s']]).all():raise ValueError('nonfinite command')
        if s['duration_s']<=settling+window:raise ValueError('segment lacks settled measurement interval')
    modes={'stop','forward','backward','left','right'}
    pairs={(a['mode'],b['mode']) for a,b in zip(segments,segments[1:])}
    if not {(a,b) for a in modes for b in modes if a!=b}<=pairs:
        raise ValueError('missing directed command transitions')
    for domain in ('fixed','randomized'):
        seeds=protocol[domain+'_seeds']
        if len(seeds)!=20 or len(set(seeds))!=20:raise ValueError('twenty unique seeds required')
    if set(protocol['fixed_seeds'])&set(protocol['randomized_seeds']):raise ValueError('seed overlap')
    if protocol['required_successes']!={'fixed':20,'randomized':18}:raise ValueError('acceptance counts changed')
    if not all(math.isfinite(v) and v>0 for v in protocol['thresholds'].values()):raise ValueError('invalid thresholds')
    return np.r_[0.,np.cumsum([s['duration_s'] for s in segments])]


def command_at(protocol,time_s):
    boundaries=validate(protocol)
    if not math.isfinite(time_s) or time_s<0 or time_s>boundaries[-1]:raise ValueError('time outside schedule')
    index=min(int(np.searchsorted(boundaries,time_s,side='right')-1),len(boundaries)-2)
    s=protocol['segments'][index]
    return index,np.array([s['vx_m_s'],0.,s['yaw_rate_rad_s']])


def score_motion(protocol,times,positions_xy,yaw_rad,*,allow_partial=False):
    boundaries=validate(protocol);t=np.asarray(times);xy=np.asarray(positions_xy);yaw=np.unwrap(yaw_rad)
    if t.ndim!=1 or xy.shape!=(len(t),2) or yaw.shape!=t.shape:raise ValueError('unaligned motion arrays')
    if not all(np.isfinite(x).all() for x in (t,xy,yaw)):raise ValueError('nonfinite motion')
    dt=np.diff(t)
    if len(dt)<2 or np.any(dt<=0) or np.max(dt)>.020000001:raise ValueError('requires complete samples at <=20 ms')
    complete=abs(t[-1]-boundaries[-1])<=1e-8
    if abs(t[0])>1e-9 or t[-1]>boundaries[-1]+1e-8 or (not complete and not allow_partial):raise ValueError('incomplete scheduled motion')
    velocity=np.diff(xy,axis=0)/dt[:,None];angle=(yaw[1:]+yaw[:-1])/2
    vx=velocity[:,0]*np.cos(angle)+velocity[:,1]*np.sin(angle)
    vy=-velocity[:,0]*np.sin(angle)+velocity[:,1]*np.cos(angle)
    rate=np.diff(yaw)/dt
    th=protocol['thresholds'];rows=[]
    for i,s in enumerate(protocol['segments']):
        start,end=boundaries[i:i+2]
        if end>t[-1]+1e-8:break
        first=int(np.argmin(abs(t-start)));last=int(np.argmin(abs(t-end)))
        if abs(t[first]-start)>1e-8 or abs(t[last]-end)>1e-8:raise ValueError('segment boundary sample missing')
        stable=np.flatnonzero((t[:-1]>=start+protocol['settling_time_s']-1e-9)&(t[1:]<=end+1e-9))
        weights=dt[stable];avg=lambda v:float(np.average(v,weights=weights))
        smooth_v=[];smooth_w=[];smooth_lateral=[]
        for j in stable:
            k=max(first,int(np.searchsorted(t,t[j+1]-protocol['velocity_smoothing_window_s'],side='left')))
            smooth_v.append(np.average(vx[k:j+1],weights=dt[k:j+1]))
            smooth_w.append(np.average(rate[k:j+1],weights=dt[k:j+1]))
            smooth_lateral.append(np.average(vy[k:j+1],weights=dt[k:j+1]))
        fwd=float(np.sum(vx[first:last]*dt[first:last]));turn=float(yaw[last]-yaw[first])
        metrics={'mean_vx_error_m_s':abs(avg(vx[stable])-s['vx_m_s']),
                 'smoothed_vx_rmse_m_s':math.sqrt(avg((np.array(smooth_v)-s['vx_m_s'])**2)),
                 'mean_yaw_rate_error_rad_s':abs(avg(rate[stable])-s['yaw_rate_rad_s']),
                 'smoothed_yaw_rate_rmse_rad_s':math.sqrt(avg((np.array(smooth_w)-s['yaw_rate_rad_s'])**2)),
                 'smoothed_lateral_velocity_rmse_m_s':math.sqrt(avg(np.array(smooth_lateral)**2)),
                 'segment_forward_displacement_error_m':abs(fwd-s['vx_m_s']*(end-start)),
                 'segment_yaw_error_rad':abs(turn-s['yaw_rate_rad_s']*(end-start))}
        if s['vx_m_s']==0:
            metrics['in_place_max_displacement_m']=float(np.max(np.linalg.norm(xy[first:last+1]-xy[first],axis=1)))
        if s['mode']=='stop':
            stable_start=stable[0]
            metrics.update(stop_planar_speed_rms_m_s=math.sqrt(avg(np.sum(velocity[stable]**2,axis=1))),
                           stop_yaw_rate_rms_rad_s=math.sqrt(avg(rate[stable]**2)),
                           stop_position_drift_m=float(np.max(np.linalg.norm(xy[stable_start:last+1]-xy[stable_start],axis=1))),
                           stop_yaw_drift_rad=float(np.max(abs(yaw[stable_start:last+1]-yaw[stable_start]))))
        failures=[k for k,v in metrics.items() if v>th[k]+1e-10]
        rows.append({'name':s['name'],'start_s':float(start),'end_s':float(end),'metrics':metrics,'violations':failures,
                     'body_forward_displacement_m':fwd,'yaw_change_rad':turn,'motion_pass':not failures})
    return {'scope':'measured motion only; physics safety must be evaluated separately',
            'complete_schedule':bool(complete),
            'motion_pass':bool(complete and all(r['motion_pass'] for r in rows)),'segments':rows}
