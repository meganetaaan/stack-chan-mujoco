#!/usr/bin/env python3
"""Sample exact hip-roll/knee motor clearance without altering either motor."""
import argparse
import hashlib
import json
from pathlib import Path
import sys


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--design', required=True, type=Path)
    p.add_argument('--out', required=True, type=Path)
    args = p.parse_args()
    import numpy as np
    design = args.design.resolve()
    sys.path[:0] = [str(design/'cad'), str(design/'src')]
    from build import build, posed
    from tab5_biped.core import all_frames, nominal
    parts = {part.name:part for part in build()}
    q0,_ = nominal()
    rows = []
    for side, offset in [('left',0),('right',5)]:
        fixed = parts[side+'_hip_roll_motor']
        moving = parts[side+'_knee_motor']
        for roll in np.linspace(-.3,.3,7):
            for pitch in np.linspace(.5,.85,15):
                q = q0.copy(); q[offset] = roll; q[offset+1] = pitch
                frames = all_frames(q)
                a = posed(fixed.shape,frames[fixed.link])
                b = posed(moving.shape,frames[moving.link])
                rows.append({'side':side,'roll_rad':float(roll),'pitch_rad':float(pitch),
                             'distance_mm':float(a.distance(b)),
                             'overlap_mm3':float(a.intersect(b).Volume())})
        print(side+' complete',flush=True)
    files = [design/name for name in ('robot.json','cad/build.py','cad/r4_geometry.py','src/tab5_biped/core.py')]
    files += [Path(__file__)]
    report = {'scope':'One motor pair per leg at sampled angles; not a continuous or full-assembly proof',
              'sha256':{str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in files},
              'rows':rows}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2)+'\n')


if __name__ == '__main__':
    main()
