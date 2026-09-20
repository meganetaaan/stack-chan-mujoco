#!/usr/bin/env python3
"""Conservative CAD check of a straight rearward battery-module extraction.

Swept bounding boxes contain every intermediate module pose; any intersection
is inconclusive (not proof of an actual collision). No hands/cables modeled.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--design',type=Path,required=True)
    p.add_argument('--mount',type=Path,required=True)
    p.add_argument('--concept',type=Path,default=Path('design/battery_mount_concept.json'))
    p.add_argument('--remove-ttl',action='store_true',help='Explicit maintenance scenario: remove TTL board before extracting battery module')
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    if a.out.exists():p.error('new output file required')
    d=a.design.resolve();sys.path[:0]=[str(d/'cad'),str(d/'src')]
    import cadquery as cq
    from build import build
    from r4_geometry import box,posed,union
    from tab5_biped.core import nominal,all_frames
    q,base=nominal();frames=all_frames(q,base)
    parts={x.name:x for x in build() if x.role!='visual'}
    parts['body_shroud'].shape=cq.importers.importStep(str(a.mount/'body_shroud.step')).val()
    module=['battery_tray','battery_2S_reservation','battery_strap_envelope']
    removed=['rear_cover','battery_M3_envelope_0','battery_M3_envelope_1']
    if a.remove_ttl:removed.append('TTL_interface')
    concept=json.loads(a.concept.read_text())
    findings=[];records=[]
    for name in module:
        shape=cq.importers.importStep(str(a.mount/(name+'.step'))).val();b=shape.BoundingBox()
        # Decompose the tray so its empty central span isn't treated as material.
        if name=='battery_tray':
            components=[concept['tray_floor']]+concept['long_walls']+concept['corner_end_stops']+concept['mount_pads']+concept['support_webs']
            boxes=[box(x['size_mm'],x['center_mm']) for x in components]
            if shape.cut(union(*boxes)).Volume()>.001:raise ValueError('tray not covered by supplied concept')
        else:boxes=[shape]
        sweeps=[]
        for part in boxes:
            bb=part.BoundingBox()
            sweeps.append(box((bb.xlen+82,bb.ylen,bb.zlen),((bb.xmin+bb.xmax)/2-41,(bb.ymin+bb.ymax)/2,(bb.zmin+bb.zmax)/2)))
        sweep=union(*sweeps)
        world=posed(sweep,frames['base'])
        for other,part in parts.items():
            if other in module or other in removed:continue
            candidate=posed(part.shape,frames[part.link])
            volume=world.intersect(candidate).Volume()
            if volume>.01:
                actual=[]
                for step in range(42):
                    shift=-2*step
                    v=posed(shape.translate((shift,0,0)),frames['base']).intersect(candidate).Volume()
                    if v>.01:actual.append({'translation_x_mm':shift,'overlap_mm3':v})
                findings.append({'module':name,'fixed_part':other,'swept_box_intersection_mm3':volume,'sampled_actual_shape_intersections':actual})
        records.append({'part':name,'initial_xmax_mm':b.xmax,'final_xmax_mm':b.xmax-82,'fully_behind_body_x_minus64':b.xmax-82 < -64})
    report={'scope':'Straight rear extraction at nominal leg pose; conservative swept boxes per tray component and per other module part',
            'translation_base_mm':[-82,0,0],'removed_before_extraction':removed,
            'preconditions':['Power disconnected, battery/electrical leads disconnected','Robot supported with legs at nominal maintenance pose','Rear cover and both mounting fasteners removed'],
            'not_verified':['Cable slack, connector disengagement and polarity','Finger/tool access and screw removal','Strap closure release and pack-only removal','Tolerance, elastic deformation, strength'],
            'swept_boxes_clear':not findings,'findings':findings,'module':records,
            'source_sha256':{str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in [Path(__file__),a.concept,d/'robot.json',d/'cad/build.py',d/'cad/r4_geometry.py',*(a.mount/(n+'.step') for n in module),a.mount/'body_shroud.step']}}
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
    return 0 if not findings else 1


if __name__=='__main__':raise SystemExit(main())
