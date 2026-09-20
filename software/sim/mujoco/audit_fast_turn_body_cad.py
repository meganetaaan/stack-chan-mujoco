#!/usr/bin/env python3
"""CAD cross-link intersection audit at saved physical trajectory poses."""
import argparse
import itertools
import json
from pathlib import Path
import sys
import numpy as np


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--poses',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--package',type=Path,default=Path('validation/fast_turn_development_v1/packaging_cad_v2'))
    a=p.parse_args()
    if a.out.exists():p.error('new output required')
    source=Path('outputs/design_r6_base_collisions').resolve()
    sys.path[:0]=[str(source/'cad'),str(source/'src')]
    import cadquery as cq
    from build import build
    from r4_geometry import posed
    original={p.name:p for p in build() if p.role!='visual'}
    package=a.package
    feet=Path('validation/fast_turn_development_v1/feet_cad_v2')
    baseline=Path('assets/r8_yaw_offset_flange_v1/cad')
    parts={n:(p.link,p.shape) for n,p in original.items() if p.link!='base'}
    for f in package.glob('*.step'):
        if f.stem.endswith('_yaw_coupler'):continue
        parts[f.stem]=('base',cq.importers.importStep(str(f)).val())
    for side,sign in [('left',1),('right',-1)]:
        pivot=np.array([-5,sign*26,62])
        for suffix in ['hip_roll_motor','fixed_roll_cradle','yaw_motor_horn','yaw_coupler']:
            name=side+'_'+suffix
            if suffix=='yaw_coupler':shape=cq.importers.importStep(str(package/(name+'.step'))).val()
            elif suffix=='hip_roll_motor':shape=original[name].shape.translate((0,sign*4,0))
            else:
                shape=cq.importers.importStep(str(baseline/(name+'.step'))).val()
                shape=shape.translate((20 if suffix=='yaw_motor_horn' else 0,sign*4,0))
            parts[name]=(side+'_hip_yaw',shape.translate(tuple(-pivot)))
        for suffix in ['foot_yoke','boot_shell','sole_TPU']:
            name=side+'_'+suffix
            parts[name]=(side+'_ankle_roll',cq.importers.importStep(str(feet/(name+'.step'))).val())
    rows=[];worst={}
    for pose in json.loads(a.poses.read_text())['rows']:
        shapes={n:posed(s,np.array(pose['frames'][link])) for n,(link,s) in parts.items()}
        boxes={n:s.BoundingBox() for n,s in shapes.items()};findings=[]
        for n1,n2 in itertools.combinations(shapes,2):
            if parts[n1][0]==parts[n2][0]:continue
            b1,b2=boxes[n1],boxes[n2]
            if any(getattr(b1,c+'max')<=getattr(b2,c+'min') or getattr(b2,c+'max')<=getattr(b1,c+'min') for c in 'xyz'):continue
            intersection=shapes[n1].intersect(shapes[n2])
            volume=float(intersection.Volume())
            if volume>.01:
                key=' / '.join(sorted([n1,n2]));findings.append({'pair':key,'volume_mm3':volume})
                if key not in worst or volume>worst[key]['volume_mm3']:
                    local=posed(intersection,np.linalg.inv(np.array(pose['frames']['base']))).BoundingBox()
                    worst[key]={'volume_mm3':volume,'time_s':pose['time_s'],
                                'intersection_bounds_base_mm':[[getattr(local,c+'min'),getattr(local,c+'max')] for c in 'xyz']}
        rows.append({'time_s':pose['time_s'],'intersections':findings})
        print(json.dumps({'time_s':pose['time_s'],'intersections':len(findings)}),flush=True)
    report={'scope':__doc__,'parts':len(parts),'rows':rows,'worst_intersections':worst,
            'limitations':['discrete saved poses','same-link pairs excluded here and reviewed separately',
                           'shaft/bearing intended interfaces must be interpreted explicitly']}
    a.out.write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
