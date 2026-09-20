#!/usr/bin/env python3
"""Export body transforms from recorded MuJoCo states for a separate CAD audit."""
import argparse
import hashlib
import json
from pathlib import Path
import mujoco
import numpy as np
from stackchan_rl.residual import runtime_xml


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--design',type=Path,required=True);p.add_argument('--trial',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);p.add_argument('--interval',type=float,default=.1)
    a=p.parse_args()
    if a.out.exists() or not np.isfinite(a.interval) or a.interval<=0:p.error('new output and positive interval required')
    scene=a.design/'models/scene.xml';states=a.trial/'states.npz'
    m=mujoco.MjModel.from_xml_string(runtime_xml(scene));d=mujoco.MjData(m)
    s=np.load(states,allow_pickle=False);rows=[]
    indices=sorted(set([0,len(s['time'])-1,*[int(np.argmin(abs(s['time']-t))) for t in np.arange(2,min(5,s['time'][-1])+1e-9,a.interval)]]))
    for i in indices:
        d.qpos[:]=s['qpos'][i];mujoco.mj_forward(m,d);frames={}
        for j in range(1,m.nbody):
            f=np.eye(4);f[:3,:3]=d.xmat[j].reshape(3,3);f[:3,3]=d.xpos[j];frames[m.body(j).name]=f.tolist()
        rows.append({'time_s':float(s['time'][i]),'frames':frames})
    r={'scope':__doc__,'rows':rows,'source_sha256':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in [Path(__file__),scene,states]}}
    a.out.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'poses':len(rows)}))


if __name__=='__main__':main()
