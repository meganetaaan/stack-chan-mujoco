#!/usr/bin/env python3
"""Derive conservative bottom-wall openings from sampled actual joint poses.

Bounds of exact slab intersections are expanded then convex-hulled per leg.
This is a sampled envelope, not a continuous sweep or structural validation.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--design', required=True, type=Path)
    p.add_argument('--trajectory', required=True, action='append', type=Path)
    p.add_argument('--stride', type=int, default=10)
    p.add_argument('--margin-mm', type=float, default=1.5)
    p.add_argument('--out', required=True, type=Path)
    args = p.parse_args()
    import numpy as np
    from scipy.spatial import ConvexHull
    if args.stride < 1 or not np.isfinite(args.margin_mm) or args.margin_mm < 0:
        p.error('stride must be positive; margin must be finite and nonnegative')
    if args.out.exists():
        p.error('output already exists')
    design = args.design.resolve()
    sys.path[:0] = [str(design/'cad'), str(design/'src')]
    from build import build, posed
    from r4_geometry import box
    from tab5_biped.core import all_frames, JOINT_NAMES
    parts = [v for v in build() if v.link != 'base' and v.role != 'visual']
    # Include inherited opening; never shrink it to fit just this experiment.
    points = json.loads((design/'docs/underside_cutouts.json').read_text())
    wall = json.loads((design/'robot.json').read_text())['body']['wall_mm']
    slab = box((128,128,wall), (0,0,wall/2))
    count = 0
    for path in args.trajectory:
        with path.open() as f:
            rows = list(csv.DictReader(f))
        if not rows:
            p.error(f'empty trajectory: {path}')
        indices = sorted(set(range(0,len(rows),args.stride)) | {len(rows)-1})
        for index in indices:
            q = np.array([float(rows[index][name]) for name in JOINT_NAMES])
            if not np.isfinite(q).all():
                p.error(f'nonfinite trajectory: {path}:{index}')
            frames = all_frames(q)
            for part in parts:
                shape = posed(part.shape, frames[part.link])
                bounds = shape.BoundingBox()
                if bounds.zmax < 0 or bounds.zmin > wall:
                    continue
                intersection = shape.intersect(slab)
                if intersection.Volume() < 1e-6:
                    continue
                b = intersection.BoundingBox()
                m = args.margin_mm
                side = part.name.split('_')[0]
                points[side].extend([[x,y] for x in (b.xmin-m,b.xmax+m)
                                     for y in (b.ymin-m,b.ymax+m)])
            count += 1
        print(f'{path.name}: {len(indices)} sampled poses', flush=True)
    polygons = {}
    for side, coordinates in points.items():
        a = np.array(coordinates)
        hull = a[ConvexHull(a).vertices]
        # Leave the outer wall and an additional 2 mm edge band untouched.
        if np.max(np.abs(hull)) > 64-wall-2:
            raise ValueError('Required opening reaches perimeter; redesign mechanism instead')
        polygons[side] = hull.tolist()
    args.out.mkdir(parents=True)
    (args.out/'underside_cutouts.json').write_text(json.dumps(polygons,indent=2)+'\n')
    files = [design/'robot.json',design/'cad/build.py',design/'cad/r4_geometry.py',
             design/'src/tab5_biped/core.py',design/'docs/underside_cutouts.json',
             Path(__file__), *args.trajectory]
    (args.out/'provenance.json').write_text(json.dumps({
        'scope':'Sampled bottom-wall envelope only; no strength or full-assembly proof',
        'sample_count':count,'stride':args.stride,'margin_mm':args.margin_mm,
        'wall_mm':wall,'manufacturing_release':False,
        'sha256':{str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in files}
    },indent=2)+'\n')


if __name__ == '__main__':
    main()
