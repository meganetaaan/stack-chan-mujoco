#!/usr/bin/env python3
"""Exact-CAD sampled clearance for a hypothetical yaw-before-roll arrangement.

Existing complete legs, roll motors and their cradles rotate together about
vertical lines. This is a geometry feasibility probe, not a connected mechanism
or an unassisted dynamics result. No brackets, shaft offsets or bearings added.
"""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import sys
import numpy as np


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--design',type=Path,required=True)
    p.add_argument('--mount',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--axis-x-mm',type=float,default=-25.)
    p.add_argument('--trim-cradle-rear',action='store_true',
                   help='remove obsolete rear fixing bridges; new yaw support remains required')
    a=p.parse_args()
    if a.out.exists() or not np.isfinite(a.axis_x_mm):p.error('new output and finite axis required')
    d=a.design.resolve();sys.path[:0]=[str(d/'cad'),str(d/'src')]
    import cadquery as cq
    from build import build
    from r4_geometry import box,posed
    from tab5_biped.core import nominal,all_frames
    q,_=nominal();frames=all_frames(q,np.eye(4))
    parts={part.name:posed(part.shape,frames[part.link]) for part in build() if part.role!='visual'}
    modified=[]
    if a.trim_cradle_rear:
        for side,y in [('left',22.),('right',-22.)]:
            name=side+'_fixed_roll_cradle';old=parts[name]
            new=old.cut(box((40,40,100),(-54,y,35))).clean()
            if not new.isValid() or len(new.Solids())!=1:raise ValueError('trimmed cradle must remain one valid solid')
            parts[name]=new
            modified.append({'part':name,'removed_volume_mm3':float(old.Volume()-new.Volume()),
                             'remaining_volume_mm3':float(new.Volume()),'disconnected_from_old_support':True})
    added=['body_shroud','battery_2S_reservation','battery_tray','battery_strap_envelope',
           'battery_M3_envelope_0','battery_M3_envelope_1']
    for name in added:parts[name]=cq.importers.importStep(str(a.mount/(name+'.step'))).val()
    parts['TTL_interface']=parts['TTL_interface'].translate((0,0,12))
    fixed={name:shape for name,shape in parts.items() if not name.startswith(('left_','right_'))}
    for side,y in [('left',22.),('right',-22.)]:
        fixed[side+'_hypothetical_yaw_case']=box((20,34,26),(a.axis_x_mm,y,75))
    legs=[{name:shape for name,shape in parts.items() if name.startswith(side+'_')} for side in ('left','right')]
    def overlaps(first,second):
        b,c=first.BoundingBox(),second.BoundingBox()
        if any(getattr(b,axis+'max')<=getattr(c,axis+'min') or getattr(c,axis+'max')<=getattr(b,axis+'min') for axis in 'xyz'):
            return 0.
        return float(first.intersect(second).Volume())
    cases=[]
    pairs=[(0.,0.)]
    for angle in (3.,6.,12.):
        pairs.extend([(angle,0.),(-angle,0.),(angle,angle),(-angle,-angle),(angle,-angle),(-angle,angle)])
    for left,right in pairs:
        moving=[]
        for leg,y,angle in zip(legs,[22.,-22.],[left,right]):
            moving.append({name:shape.rotate((a.axis_x_mm,y,0),(a.axis_x_mm,y,1),angle) for name,shape in leg.items()})
        findings=[]
        comparisons=itertools.chain(itertools.product(moving[0].items(),fixed.items()),
                                    itertools.product(moving[1].items(),fixed.items()),
                                    itertools.product(moving[0].items(),moving[1].items()))
        for (first,s1),(second,s2) in comparisons:
            volume=overlaps(s1,s2)
            if volume>.01:findings.append({'part1':first,'part2':second,'overlap_mm3':volume})
        cases.append({'yaw_deg':[left,right],'intersections':findings,'sample_clear':not findings})
        print(json.dumps({'yaw_deg':[left,right],'intersecting_pairs':len(findings)}),flush=True)
    sources=[Path(__file__),d/'robot.json',d/'cad/build.py',d/'cad/r4_geometry.py',d/'src/tab5_biped/core.py',
             *[a.mount/(name+'.step') for name in added]]
    report={'scope':__doc__,'axis_base_x_mm':a.axis_x_mm,'axis_base_y_mm':[22,-22],
            'trimmed_cradle_rear':a.trim_cradle_rear,'modified_parts':modified,
            'TTL_shift_z_mm':12,'joint_pose_rad':q.tolist(),'intersection_threshold_mm3':.01,
            'not_verified':['shaft-to-case offset','continuous swept volume between samples','other leg joint poses',
                            'connected mounts and bearings','dynamics and strength'],
            'source_sha256':{str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in sources},'cases':cases}
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,indent=2)+'\n')
    if a.trim_cradle_rear:
        for item in modified:
            cq.exporters.export(parts[item['part']],str(a.out.with_name(a.out.stem+'_'+item['part']+'.step')))


if __name__=='__main__':main()
