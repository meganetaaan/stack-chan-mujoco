#!/usr/bin/env python3
"""Replay joint poses without dynamics to inspect MuJoCo self-contact coverage.

Base is raised above the floor; internal contacts are rigid-transform invariant.
No claim about walking stability or real-world contact forces is made.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import mujoco


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--design',required=True,type=Path)
    p.add_argument('--trajectory',required=True,type=Path)
    p.add_argument('--rows',type=int,nargs='+',required=True)
    p.add_argument('--out',required=True,type=Path)
    args = p.parse_args()
    path = args.design/'models/scene.xml'
    model = mujoco.MjModel.from_xml_path(str(path.resolve()))
    data = mujoco.MjData(model)
    with args.trajectory.open() as f:
        trajectory = list(csv.DictReader(f))
    names = [f'{side}_{joint}' for side in ('left','right')
             for joint in ('hip_roll','hip_pitch','knee','ankle_pitch','ankle_roll')]
    results = []
    for row in args.rows:
        if not 0 <= row < len(trajectory):
            p.error('row outside trajectory')
        mujoco.mj_resetDataKeyframe(model,data,model.key('home').id)
        data.qpos[2] = 10
        for name in names:
            value = float(trajectory[row][name])
            if not math.isfinite(value):
                p.error('nonfinite joint pose')
            data.qpos[model.joint(name).qposadr[0]] = value
        mujoco.mj_forward(model,data)
        hits = []
        for i in range(data.ncon):
            contact = data.contact[i]
            if contact.dist < -1e-8:
                hits.append({'a':model.geom(contact.geom1).name,'b':model.geom(contact.geom2).name,
                             'depth_mm':float(-1000*contact.dist)})
        results.append({'row':row,'time_s':float(trajectory[row]['time_s']),'contacts':hits})
        print(row,len(hits),flush=True)
    report = {'scope':'Static internal contact replay, no stability or contact-force proof',
              'model_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
              'trajectory_sha256':hashlib.sha256(args.trajectory.read_bytes()).hexdigest(),
              'replay_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'results':results}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2)+'\n')


if __name__ == '__main__':
    main()
