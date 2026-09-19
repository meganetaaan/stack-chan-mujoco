#!/usr/bin/env python3
"""Reconstruct terminal self contacts from a recorded R6 trial (not a rerun)."""
import argparse
import json
from pathlib import Path
import mujoco
import numpy as np
from stackchan_rl.r6_factory import make_env
from stackchan_rl.residual import STATE_SPEC, sha


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--batch',type=Path,required=True)
    p.add_argument('--trial',required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    if a.out.exists():p.error('new output path required')
    folder=a.batch/a.trial;r=json.loads((folder/'report.json').read_text())
    if r['failure']!='self_collision':raise ValueError('not a self-collision termination')
    config=json.loads((a.batch/'config.json').read_text())
    if sha(folder/'states.npz')!=r['trajectory_sha256']:raise ValueError('state hash mismatch')
    env=make_env(config)
    try:
        if json.dumps(env.fingerprint,sort_keys=True)!=json.dumps(r['interface'],sort_keys=True):raise ValueError('source/model mismatch')
        env.reset(seed=r['seed'],options={'randomize':r['domain']=='randomized'})
        if env.parameters!=r['parameters']:raise ValueError('plant reconstruction mismatch')
        with np.load(folder/'states.npz',allow_pickle=False) as z:state=z['state'][-1].copy()
        mujoco.mj_setState(env.model,env.data,state,STATE_SPEC)
        mujoco.mj_forward(env.model,env.data)
        contacts=[]
        for contact in env.data.contact:
            i,j=map(int,contact.geom)
            if env.floor in (i,j):continue
            contacts.append({'geom1':env.model.geom(i).name,'geom2':env.model.geom(j).name,
                             'body1':env.model.body(int(env.model.geom_bodyid[i])).name,
                             'body2':env.model.body(int(env.model.geom_bodyid[j])).name,
                             'signed_distance_m':float(contact.dist),'position_world_m':contact.pos.tolist()})
        result={'scope':'Terminal saved-state contact reconstruction; no integration rerun, independent CAD validation or logged substep force claim',
                'time_s':float(env.data.time),'seed':r['seed'],'contacts':contacts,
                'sources':{'report_sha256':sha(folder/'report.json'),'states_sha256':sha(folder/'states.npz'),
                           'script_sha256':sha(__file__),'interface':env.fingerprint}}
        a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(contacts,indent=2))
    finally:env.close()


if __name__=='__main__':main()
