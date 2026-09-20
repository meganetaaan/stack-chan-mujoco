#!/usr/bin/env python3
"""Cover omitted fixed cradles and mass reservations in a separate MJCF copy.

No geometry, inertia, actuator or joint changes. The reservations remain
packaging assumptions, not validated battery/electronics mounting designs.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import xml.etree.ElementTree as ET


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def cradle_boxes(y):
    # Reviewed R6 outer box minus the wide central slot and lower-lip relief.
    boxes=[]
    for side in (-1,1):
        for lo,hi,bottom in [(-34.,-14.5,14.),(-14.5,-7.5,17.),(-7.5,-4.,14.)]:
            boxes.append(((hi-lo,1.4,52.-bottom),((lo+hi)/2,y+side*11.3,(52.+bottom)/2)))
    boxes.append(((30.,21.2,2.5),(-19.,y,50.75)))
    boxes.extend([((6.2,24.,2.4),(-35.1,y,z)) for z in (51.,15.5)])
    return boxes


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--design',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);a=p.parse_args();design=a.design.resolve()
    if a.out.exists():p.error('use a new output directory')
    sys.path[:0]=[str(design/'cad'),str(design/'src')]
    from build import build
    from r4_geometry import box,union
    from tab5_biped.core import KIN
    if KIN['hip_roll_x_mm']!=-6 or KIN['hip_roll_height_mm']!=25:
        p.error('cradle decomposition requires the reviewed R6 origins')
    parts={part.name:part for part in build()}
    root=ET.parse(design/'models/scene.xml').getroot();body=root.find(".//body[@name='base']")
    records=[]
    names=['left_fixed_roll_cradle','right_fixed_roll_cradle','battery_2S_reservation',
           'dedicated_5V_converter','TTL_interface','cables_and_fasteners']
    for name in names:
        part=parts[name];prefix='col_'+name+'_'
        if part.link!='base' or any(g.get('name','').startswith(prefix) for g in root.findall('.//geom')):
            p.error(f'{name}: wrong link or already covered')
        if name.endswith('fixed_roll_cradle'):
            y=(1 if name.startswith('left') else -1)*KIN['hip_half_spacing_mm'];boxes=cradle_boxes(y)
        else:
            b=part.shape.BoundingBox()
            boxes=[((b.xlen,b.ylen,b.zlen),((b.xmin+b.xmax)/2,(b.ymin+b.ymax)/2,(b.zmin+b.zmax)/2))]
        combined=union(*(box(size,center) for size,center in boxes))
        missing=part.shape.cut(combined).Volume();extra=combined.cut(part.shape).Volume()
        if missing>.001 or not combined.isValid():raise ValueError(f'{name}: uncovered CAD volume {missing}')
        for i,(size,center) in enumerate(boxes):
            ET.SubElement(body,'geom',name=prefix+str(i),type='box',size=' '.join(f'{x/2000:.12g}' for x in size),
                pos=' '.join(f'{x/1000:.12g}' for x in center),**{'class':'collision'})
        records.append({'part':name,'convex_boxes':len(boxes),'cad_volume_mm3':part.shape.Volume(),
            'uncovered_volume_mm3':missing,'extra_volume_mm3':extra,'boxes_mm':boxes})
        print(name,'missing',missing,'extra',extra,flush=True)
    root.set('model',root.get('model')+'-base-reservations')
    shutil.copytree(design,a.out,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    # A copied frozen-file manifest would incorrectly describe the new XML.
    frozen=a.out/'FROZEN_FILES.json'
    if frozen.exists():frozen.unlink()
    ET.indent(root,space='  ');ET.ElementTree(root).write(a.out/'models/scene.xml',encoding='utf-8',xml_declaration=True)
    report={'scope':'Additional conservative fixed-cradle and reservation collisions; no dynamics run by this script',
        'physics_validated':False,'CAD_inertia_joints_actuators_unchanged':True,
        'source_model_sha256':sha(design/'models/scene.xml'),'output_model_sha256':sha(a.out/'models/scene.xml'),
        'source_sha256':{name:sha(design/name) for name in ('robot.json','cad/build.py','cad/r4_geometry.py')},
        'augmentation_source_sha256':sha(__file__),'coverage_tolerance_mm3':.001,'parts':records}
    (a.out/'BASE_COLLISION_PATCH.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
