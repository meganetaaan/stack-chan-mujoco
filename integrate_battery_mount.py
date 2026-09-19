#!/usr/bin/env python3
"""Create a separate mounted-battery MJCF with CAD-derived base inertia.

Leg geometry, joints and actuator parameters are retained byte-for-byte in XML.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import xml.etree.ElementTree as ET


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--design', type=Path, required=True)
    p.add_argument('--mount', type=Path, required=True)
    p.add_argument('--concept', type=Path, default=Path('design/battery_mount_concept.json'))
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    if a.out.exists(): p.error('use a new output directory')
    design = a.design.resolve()
    sys.path[:0] = [str(design/'cad'),str(design/'src')]
    import cadquery as cq
    import numpy as np
    from build import build
    from r4_geometry import Part, box, union, mass_properties
    from tab5_biped.core import PARAMS
    c = json.loads(a.concept.read_text())
    # The v2 strap was designed for this particular reservation geometry.
    if c['battery_center_base_mm'] != [-1,0,80] or c['battery_size_mm'] != [20.5,70.4,38.4] or c['strap']['width_mm'] != 8:
        raise ValueError('strap decomposition requires reviewed v2 concept')
    parts = {x.name:x for x in build() if x.link=='base' and x.role!='visual'}
    old_base = list(parts.values())
    def aggregate(items):
        values = [mass_properties(x) for x in items]
        mass = sum(x[0] for x in values)
        com = sum(m*r for m,r,_ in values)/mass
        inertia = sum(I+m*(np.dot(r-com,r-com)*np.eye(3)-np.outer(r-com,r-com)) for m,r,I in values)
        return {'mass_kg':float(mass),'com_m':com.tolist(),'inertia_kg_m2':inertia.tolist()}
    old = aggregate(old_base)
    stored = json.loads((design/'models/inertials.json').read_text())
    for key in ('mass_kg','com_m','inertia_kg_m2'):
        if not np.allclose(old[key], stored['base'][key], rtol=1e-9, atol=1e-12):
            raise ValueError(f'input CAD and base inertial disagree: {key}')
    changed = ['body_shroud','battery_2S_reservation','battery_tray','battery_strap_envelope','battery_M3_envelope_0','battery_M3_envelope_1']
    shapes = {n:cq.importers.importStep(str(a.mount/(n+'.step'))).val() for n in changed}
    for n in ('body_shroud','battery_2S_reservation'):
        source = parts[n]
        parts[n] = Part(n,'base',shapes[n],source.role,source.color,source.mass)
    for n,mass in [('battery_tray',None),('battery_strap_envelope',c['strap']['mass_assumption_kg']),
                   ('battery_M3_envelope_0',c['fasteners']['mass_assumption_each_kg']),('battery_M3_envelope_1',c['fasteners']['mass_assumption_each_kg'])]:
        parts[n] = Part(n,'base',shapes[n],'custom',(.25,.25,.3),mass)
    new = aggregate(parts.values())
    expected = json.loads((a.mount/'report.json').read_text())['total_mass_delta_kg']
    if abs(new['mass_kg']-old['mass_kg']-expected)>1e-10: raise ValueError('mass accounting mismatch')
    root = ET.parse(design/'models/scene.xml').getroot()
    base = root.find(".//body[@name='base']"); asset = root.find('asset')
    inertial = base.find('inertial'); I=np.array(new['inertia_kg_m2'])
    fmt=lambda xs:' '.join(f'{x:.15g}' for x in xs)
    inertial.attrib.clear()
    inertial.attrib.update(mass=str(new['mass_kg']),pos=fmt(new['com_m']),fullinertia=fmt([I[0,0],I[1,1],I[2,2],I[0,1],I[0,2],I[1,2]]))
    for geom in list(base.findall('geom')):
        if geom.get('name','').startswith('col_battery_2S_reservation_'): base.remove(geom)
    models=a.out/'models'; (models/'meshes').mkdir(parents=True)
    shutil.copytree(design/'models/meshes',models/'meshes',dirs_exist_ok=True)
    for n in changed:
        cq.exporters.export(shapes[n],str(models/'meshes'/(n+'.stl')),tolerance=.09,angularTolerance=.15)
        if n not in ('body_shroud','battery_2S_reservation'):
            ET.SubElement(asset,'mesh',name=n+'_mesh',file=n+'.stl',scale='.001 .001 .001')
            ET.SubElement(base,'geom',name=n+'_visual',type='mesh',mesh=n+'_mesh',contype='0',conaffinity='0',group='2',rgba='.25 .25 .3 1',mass='0')
    coverage=[]
    def add_boxes(name,boxes):
        cover=union(*(box(size,center) for size,center in boxes))
        missing=shapes[name].cut(cover).Volume()
        if missing>.001: raise ValueError(f'{name}: uncovered {missing}')
        for i,(size,center) in enumerate(boxes):
            ET.SubElement(base,'geom',name=f'col_{name}_{i}',type='box',size=fmt(np.array(size)/2000),pos=fmt(np.array(center)/1000),**{'class':'collision'})
        coverage.append({'part':name,'boxes':len(boxes),'uncovered_mm3':missing,'extra_mm3':cover.cut(shapes[name]).Volume()})
    comps=[c['tray_floor']]+c['long_walls']+c['corner_end_stops']+c['mount_pads']+c['support_webs']
    add_boxes('battery_tray',[(x['size_mm'],x['center_mm']) for x in comps])
    for n in ('battery_2S_reservation','battery_M3_envelope_0','battery_M3_envelope_1'):
        b=shapes[n].BoundingBox()
        add_boxes(n,[((b.xlen,b.ylen,b.zlen),((b.xmin+b.xmax)/2,(b.ymin+b.ymax)/2,(b.zmin+b.zmax)/2))])
    outer=[(-13.65,58.8),(11.65,58.8),(11.65,69),(9.75,99.7),(-11.75,99.7),(-13.65,69)]
    inner=[(-13.15,59.3),(11.15,59.3),(11.15,68.8),(9.25,99.2),(-11.25,99.2),(-13.15,68.8)]
    segments=[]
    from scipy.spatial import ConvexHull
    for i in range(6):
        j=(i+1)%6; polygon=[outer[i],outer[j],inner[j],inner[i]]
        segment=cq.Workplane('XZ').polyline(polygon).close().extrude(8).val().translate((0,4,0))
        vertices=np.array([(x,y,z) for y in (-4,4) for x,z in polygon])
        if abs(ConvexHull(vertices).volume-segment.Volume())>.001: raise ValueError('nonconvex strap segment')
        name=f'col_battery_strap_{i}'
        ET.SubElement(asset,'mesh',name=name+'_mesh',vertex=fmt(vertices.ravel()/1000))
        ET.SubElement(base,'geom',name=name,type='mesh',mesh=name+'_mesh',**{'class':'collision'})
        segments.append(segment)
    cover=union(*segments);missing=shapes['battery_strap_envelope'].cut(cover).Volume()
    if missing>.001: raise ValueError('uncovered strap')
    coverage.append({'part':'battery_strap_envelope','convex_segments':6,'uncovered_mm3':missing,'extra_mm3':cover.cut(shapes['battery_strap_envelope']).Volume()})
    root.set('model',root.get('model')+'-mounted-battery')
    ET.indent(root,space='  '); ET.ElementTree(root).write(models/'scene.xml',encoding='utf-8',xml_declaration=True)
    robot=json.loads((design/'robot.json').read_text());robot['revision']+='-mounted-battery'
    robot['battery_envelope']['center_base_mm']=c['battery_center_base_mm']
    robot['battery_envelope']['mass_note']='103 g case reservation; tray CAD mass and assumed strap/fastener masses added separately'
    robot['battery_envelope']['placement_note']='Internal tray and retention envelopes included; connector, closure, extraction and strength remain unverified'
    robot['battery_mount']={'scope':'CAD envelopes, not identified hardware','mass_delta_kg':expected,'center_base_mm':c['battery_center_base_mm']}
    (a.out/'robot.json').write_text(json.dumps(robot,indent=2)+'\n')
    stored['base']=new; (models/'inertials.json').write_text(json.dumps(stored,indent=2)+'\n')
    shutil.copy2(design/'models/joint_map.json',models/'joint_map.json')
    records=[]
    for n,part in parts.items():
        m,r,I=mass_properties(part);records.append({'part':n,'mass_kg':m,'com_base_m':r.tolist(),'inertia_com_kg_m2':I.tolist()})
    result={'scope':'Mounted battery MJCF only; no URDF or dynamics acceptance claim',
            'old_base':old,'new_base':new,'total_mass_delta_kg':expected,'collision_coverage':coverage,'base_parts':records,
            'source_sha256':{str(x):sha(x) for x in [Path(__file__),a.concept,design/'models/scene.xml',design/'robot.json',design/'cad/build.py',design/'cad/r4_geometry.py']},
            'mount_sha256':{n:sha(a.mount/(n+'.step')) for n in changed},
            'limitations':['tray bolt holes conservatively filled in collisions','fastener collision boxes overcover shaft spaces','body rail collision approximation unchanged','strap closure and strength unverified','electrical compatibility unverified']}
    (a.out/'BATTERY_MOUNT_PATCH.json').write_text(json.dumps(result,indent=2)+'\n')
    files={str(x.relative_to(a.out)):sha(x) for x in sorted(a.out.rglob('*')) if x.is_file()}
    (a.out/'FROZEN_FILES.json').write_text(json.dumps({'scope':'mounted battery model snapshot','files':files},indent=2)+'\n')
    print(json.dumps({'old_base':old,'new_base':new,'mass_delta_kg':expected,'coverage':coverage},indent=2))


if __name__=='__main__': main()
