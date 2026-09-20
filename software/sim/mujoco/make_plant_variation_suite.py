#!/usr/bin/env python3
"""Reproduce the fixed exploratory 20-case uncertainty suite."""
import argparse
import json
from pathlib import Path
import random


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',required=True,type=Path)
    args = p.parse_args()
    if args.out.exists():
        p.error('output already exists')
    args.out.mkdir(parents=True)
    rng = random.Random(20260919)
    bounds = {'mass_scale':(.95,1.05),'sliding_friction':(.6,1.),'torque_scale':(.9,1.),
              'speed_scale':(.95,1.05),'extra_delay_s':(0,.004)}
    values = {}
    for key,(lo,hi) in bounds.items():
        x = [lo+(hi-lo)*(i+rng.random())/20 for i in range(20)]
        rng.shuffle(x);values[key] = x
    manifest = {'seed':20260919,
                'scope':'Exploratory assumed uncertainty; not measured distributions or hardware acceptance',
                'bounds':bounds,'cases':[]}
    for i in range(20):
        value = {key:values[key][i] for key in bounds}
        value['initial_joint_offset_rad'] = [rng.uniform(-.005,.005) for _ in range(10)]
        name = f'case_{i:02d}.json'
        (args.out/name).write_text(json.dumps(value,indent=2)+'\n')
        manifest['cases'].append(name)
    (args.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (args.out/'identity.json').write_text('{}\n')


if __name__ == '__main__':
    main()
