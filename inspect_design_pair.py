#!/usr/bin/env python3
"""Measure CAD distance and overlap for one pair at a recorded joint pose."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--design', required=True, type=Path)
    p.add_argument('--trajectory-csv', required=True, type=Path)
    p.add_argument('--parts', required=True, nargs=2)
    p.add_argument('--out', required=True, type=Path)
    p.add_argument('--row', type=int, default=-1, help='Zero-based CSV data row; default last')
    args = p.parse_args()
    import numpy as np
    design = args.design.resolve()
    sys.path[:0] = [str(design/'cad'), str(design/'src')]
    from build import build, posed
    from tab5_biped.core import all_frames, JOINT_NAMES
    with args.trajectory_csv.open() as f:
        rows = list(csv.DictReader(f))
    if not rows:
        p.error('empty trajectory')
    if not -len(rows) <= args.row < len(rows):
        p.error('row outside trajectory')
    row = rows[args.row]
    q = np.array([float(row[name]) for name in JOINT_NAMES])
    if not np.isfinite(q).all():
        p.error('nonfinite terminal joint pose')
    parts = {part.name:part for part in build()}
    if any(name not in parts for name in args.parts) or args.parts[0] == args.parts[1]:
        p.error('specify two distinct existing CAD part names')
    frames = all_frames(q)
    selected = [parts[name] for name in args.parts]
    shapes = [posed(part.shape,frames[part.link]) for part in selected]
    overlap = shapes[0].intersect(shapes[1])
    volume = float(overlap.Volume())
    bounds = {}
    if volume > 0:
        for part in selected:
            b = posed(overlap,np.linalg.inv(frames[part.link])).BoundingBox()
            bounds[part.name] = {'link':part.link,
                'min_mm':[b.xmin,b.ymin,b.zmin], 'max_mm':[b.xmax,b.ymax,b.zmax]}
    files = [design/name for name in ('robot.json','cad/build.py','cad/r4_geometry.py',
                                      'src/tab5_biped/core.py','docs/underside_cutouts.json')]
    files += [args.trajectory_csv,Path(__file__)]
    report = {'scope':'Exact CAD pair at one recorded sample; numerical kernel tolerances apply',
              'parts':args.parts,'row':args.row % len(rows),'time_s':float(row['time_s']),'q_rad':q.tolist(),
              'distance_mm':float(shapes[0].distance(shapes[1])),
              'overlap_mm3':volume,'overlap_bounds_local':bounds,
              'sha256':{str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in files}}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2)+'\n')
    print(f'distance={report["distance_mm"]:.6g} mm overlap={volume:.6g} mm3')


if __name__ == '__main__':
    main()
