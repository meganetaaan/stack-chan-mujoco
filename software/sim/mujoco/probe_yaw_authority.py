#!/usr/bin/env python3
"""Measure yaw response to small joint-target offsets through actual physics.

Plant characterization with a fixed reference, NOT RL or acceptance evidence.
"""
import os
for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):os.environ[k]='1'
import argparse
from concurrent.futures import ProcessPoolExecutor
import json
import multiprocessing
from pathlib import Path
import numpy as np
from stackchan_rl.residual import sha
from stackchan_rl.r6_factory import make_env

CHANNELS={'hip_pitch_difference':{1:1,6:-1},'knee_difference':{2:1,7:-1},
          'ankle_pitch_difference':{3:1,8:-1},'hip_roll_common':{0:1,5:1},
          'ankle_roll_common':{4:1,9:1}}


def run(job):
    name,channel,sign,config,out=job
    folder=Path(out)/name;folder.mkdir()
    env=make_env(config,record=True);obs,info=env.reset(seed=71234,options={'randomize':False})
    action=np.zeros(10)
    if channel is not None:
        for joint,gain in CHANNELS[channel].items():action[joint]=sign*.5*gain
    times=[];angles=[]
    while True:
        _,_,done,truncated,info=env.step(action)
        rot=env.data.xmat[env.base].reshape(3,3)
        times.append(float(env.data.time));angles.append(float(np.arctan2(rot[1,0],rot[0,0])))
        if done or truncated:break
    times=np.asarray(times);angles=np.unwrap(angles);late=times>=3.
    slope=float(np.polyfit(times[late],angles[late],1)[0]) if np.count_nonzero(late)>20 else None
    env.save_trajectory(folder/'states.npz')
    report={'scope':'constant joint offset characterization, not trained control or acceptance',
        'controller':'reference_with_constant_joint_offset','domain':'fixed','seed':71234,
        'channel':channel,'action':action.tolist(),'target_offset_rad':(action*config['residual_scale_rad']).tolist(),
        'late_yaw_rate_rad_s':slope,'final_yaw_deg':float(np.rad2deg(angles[-1])),**info,
        'interface':env.fingerprint,'trajectory_sha256':sha(folder/'states.npz'),
        'probe_source_sha256':sha(__file__)}
    (folder/'report.json').write_text(json.dumps(report,indent=2)+'\n');env.close()
    return {k:report[k] for k in ('channel','action','failure','time_s','forward_m','late_yaw_rate_rad_s','final_yaw_deg')}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--design',required=True)
    p.add_argument('--out',type=Path,required=True);p.add_argument('--workers',type=int,default=4)
    a=p.parse_args()
    if a.out.exists():p.error('use a new output directory')
    c=json.loads(Path('configs/r6/heading_residual.json').read_text());c.update(design=a.design,episode_s=6.,randomize=False)
    a.out.mkdir(parents=True);(a.out/'config.json').write_text(json.dumps(c,indent=2)+'\n')
    jobs=[('zero',None,0,c,str(a.out))]+[(f'{ch}_{sign:+d}',ch,sign,c,str(a.out)) for ch in CHANNELS for sign in (-1,1)]
    with ProcessPoolExecutor(max_workers=a.workers,mp_context=multiprocessing.get_context('spawn')) as pool:
        results=list(pool.map(run,jobs))
    (a.out/'summary.json').write_text(json.dumps({'scope':'yaw authority characterization only','results':results},indent=2)+'\n')
    for r in results:print(json.dumps(r),flush=True)

if __name__=='__main__':main()
