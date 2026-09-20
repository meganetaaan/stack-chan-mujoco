#!/usr/bin/env python3
"""Describe a recorded joint-limit termination without modifying the trial."""
import argparse
import hashlib
import json
from pathlib import Path
import mujoco
import numpy as np


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--trial',type=Path,required=True)
    p.add_argument('--model',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    if a.out.exists():p.error('new output path required')
    r=json.loads((a.trial/'report.json').read_text())
    if r['failure']!='joint_limit':raise ValueError('not a joint-limit termination')
    if sha(a.trial/'states.npz')!=r['trajectory_sha256']:raise ValueError('state hash mismatch')
    if sha(a.model)!=r['interface']['model_sha256']:raise ValueError('model hash mismatch')
    m=mujoco.MjModel.from_xml_path(str(a.model.resolve()))
    with np.load(a.trial/'states.npz',allow_pickle=False) as z:
        s=z['state'];obs=z['observation']
        names=r['interface']['joint_order']
        terminal=[]
        for i,n in enumerate(names):
            joint=m.joint(n);column=1+int(joint.qposadr[0]);q=float(s[-1,column])
            lower,upper=map(float,joint.range);margin=min(q-lower,upper-q)
            row={'joint':n,'terminal_q_rad':q,'limits_rad':[lower,upper],
                 'signed_margin_rad':margin,
                 'controller_filtered_target_rad':float(obs[-1,i]+obs[-1,49+i]),
                 'note':'filtered controller target before motor delay; not a causal explanation'}
            if margin<0:
                indices=np.flatnonzero(s[:,0]>=s[-1,0]-1.)
                row['last_second_saved_samples']=[{'time_s':float(s[j,0]),'q_rad':float(s[j,column])} for j in indices]
            terminal.append(row)
    result={'scope':'Recorded joint angles and nominal limits; no dynamics rerun or root-cause claim',
            'time_s':float(s[-1,0]),'joints':terminal,
            'sources':{'report_sha256':sha(a.trial/'report.json'),'states_sha256':sha(a.trial/'states.npz'),
                       'model_sha256':sha(a.model),'script_sha256':sha(__file__)}}
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps([{k:v for k,v in row.items() if k!='last_second_saved_samples'} for row in terminal if row['signed_margin_rad']<0],indent=2))


if __name__=='__main__':main()
