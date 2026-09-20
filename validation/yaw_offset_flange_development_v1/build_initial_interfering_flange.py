#!/usr/bin/env python3
"""Build a separate 12-axis dynamics candidate with explicit CAD mass accounting.

Support/horn shapes and shaft location are engineering placeholders, not a
manufacturing release or hardware-verified mechanism. Never acceptance evidence.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import sys
import xml.etree.ElementTree as ET
import numpy as np


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cad-design',type=Path,required=True)
    p.add_argument('--baseline',type=Path,default=Path('assets/r6_mounted_battery'))
    p.add_argument('--mount',type=Path,default=Path('validation/battery_mount_review_v2'))
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--manufacturer-yaw-layout',action='store_true',help='correct yaw shaft offset and add a drilled output flange; mounting remains provisional')
    a=p.parse_args()
    if a.out.exists():p.error('new output required')
    d=a.cad_design.resolve();sys.path[:0]=[str(d/'cad'),str(d/'src')]
    import cadquery as cq
    from build import build
    from r4_geometry import Part,box,cyl,union,mass_properties
    source_parts={part.name:part for part in build() if part.role!='visual'}
    records={r['part']:r for r in json.loads((a.baseline/'BATTERY_MOUNT_PATCH.json').read_text())['base_parts']}
    def aggregate(items,offset=np.zeros(3)):
        mass=sum(r['mass_kg'] for r in items)
        com=sum(r['mass_kg']*np.array(r['com_base_m']) for r in items)/mass
        inertia=sum(np.array(r['inertia_com_kg_m2'])+r['mass_kg']*((np.array(r['com_base_m'])-com)@(np.array(r['com_base_m'])-com)*np.eye(3)-np.outer(np.array(r['com_base_m'])-com,np.array(r['com_base_m'])-com)) for r in items)
        return {'mass_kg':float(mass),'com_m':(com-offset).tolist(),'inertia_kg_m2':inertia.tolist()}
    stored=json.loads((a.baseline/'models/inertials.json').read_text())
    old_base=aggregate(list(records.values()))
    for key in old_base:
        if not np.allclose(old_base[key],stored['base'][key],rtol=1e-10,atol=1e-12):raise ValueError('baseline component mass mismatch')
    a.out.mkdir(parents=True);shutil.copytree(a.baseline/'models',a.out/'models')
    cad=a.out/'cad';cad.mkdir()
    root=ET.parse(a.baseline/'models/scene.xml').getroot()
    root.set('model','r7-yaw-candidate-unverified-support')
    base=root.find(".//body[@name='base']");asset=root.find('asset')
    fmt=lambda x:' '.join(f'{v:.15g}' for v in x)
    def set_inertial(body,record):
        old=body.find('inertial')
        if old is not None:body.remove(old)
        I=np.array(record['inertia_kg_m2'])
        ET.SubElement(body,'inertial',mass=str(record['mass_kg']),pos=fmt(record['com_m']),
                      fullinertia=fmt([I[0,0],I[1,1],I[2,2],I[0,1],I[0,2],I[1,2]]))
    def record_shape(name,shape,mass=None):
        part=Part(name,'base',shape,'custom',(.25,.3,.35),mass)
        m,r,I=mass_properties(part)
        return {'part':name,'mass_kg':m,'com_base_m':r.tolist(),'inertia_com_kg_m2':I.tolist()}
    def visual(body,name,shape,offset=np.zeros(3)):
        cq.exporters.export(shape,str(cad/(name+'.step')))
        file=name+'.stl';cq.exporters.export(shape,str(a.out/'models/meshes'/file),tolerance=.09,angularTolerance=.15)
        mesh=asset.find(f"mesh[@name='{name}_mesh']")
        if mesh is None:ET.SubElement(asset,'mesh',name=name+'_mesh',file=file,scale='.001 .001 .001')
        ET.SubElement(body,'geom',name='vis_'+name,type='mesh',mesh=name+'_mesh',pos=fmt(-offset),
                      rgba='.25 .3 .35 1',contype='0',conaffinity='0',group='2',mass='0')
    def collision_box(body,name,size,center,offset=np.zeros(3)):
        return ET.SubElement(body,'geom',name='col_'+name,type='box',size=fmt(np.array(size)/2000),
                             pos=fmt(np.array(center)/1000-offset),**{'class':'collision'})
    concept_path=Path('design/battery_mount_concept.json')
    concept=json.loads(concept_path.read_text())
    tray=cq.importers.importStep(str(a.mount/'battery_tray.step')).val()
    old_webs=union(*(box(c['size_mm'],c['center_mm']) for c in concept['support_webs']))
    webs=[]
    for sign in (-1,1):
        webs.extend([((11,2.4,6),(-38.5,sign*22,57.6)),
                     ((2.4,10.4,6),(-34,sign*26,57.6)),
                     ((18,2.4,6),(-25,sign*30,57.6)),
                     ((2.4,10.4,6),(-16,sign*26,57.6)),
                     ((4.35,2.4,6),(-13.825,sign*22,57.6))])
    tray=union(tray.cut(old_webs),*(box(size,center) for size,center in webs))
    if not tray.isValid() or len(tray.Solids())!=1:raise ValueError('rerouted tray must remain connected')
    records['battery_tray']=record_shape('battery_tray',tray)
    cq.exporters.export(tray,str(cad/'battery_tray.step'))
    cq.exporters.export(tray,str(a.out/'models/meshes/battery_tray.stl'),tolerance=.09,angularTolerance=.15)
    for geom in list(base.findall('geom')):
        if geom.get('name') in ('col_battery_tray_9','col_battery_tray_10'):base.remove(geom)
    for i,(size,center) in enumerate(webs):collision_box(base,'battery_yaw_detour_'+str(i),size,center)
    records['TTL_interface']['com_base_m'][2]+=.012
    for geom in base.findall('geom'):
        if 'TTL_interface' in geom.get('name',''):
            xyz=np.fromstring(geom.get('pos','0 0 0'),sep=' ');xyz[2]+=.012;geom.set('pos',fmt(xyz))
    flag=root.find('option/flag')
    if flag is None or flag.get('filterparent')!='disable':
        raise ValueError('parent-child collision filtering must remain disabled')
    new_parts=[];yaw_bodies=[]
    for side,y in [('left',22.),('right',-22.)]:
        pivot=np.array([-.025,y/1000,.062])
        yaw=ET.SubElement(base,'body',name=side+'_hip_yaw',pos=fmt(pivot))
        ET.SubElement(yaw,'joint',name=side+'_hip_yaw',axis='0 0 1',range='-.09 .09',**{'class':'joint_defaults'})
        leg=base.find(f"body[@name='{side}_hip_roll']");base.remove(leg)
        leg.set('pos',fmt(np.fromstring(leg.get('pos'),sep=' ')-pivot));yaw.append(leg)
        moving_records=[records.pop(side+'_hip_roll_motor')]
        records.pop(side+'_fixed_roll_cradle')
        cradle=source_parts[side+'_fixed_roll_cradle'].shape.cut(box((40,40,100),(-54,y,35))).clean()
        if not cradle.isValid() or len(cradle.Solids())!=1:raise ValueError('invalid cradle')
        moving_records.append(record_shape(side+'_fixed_roll_cradle',cradle))
        for geom in list(base.findall('geom')):
            name=geom.get('name','')
            if side+'_hip_roll_motor' in name or side+'_fixed_roll_cradle' in name:
                base.remove(geom)
                if name=='vis_'+side+'_fixed_roll_cradle':continue
                pos=np.fromstring(geom.get('pos','0 0 0'),sep=' ')
                if name.startswith('col_'+side+'_fixed_roll_cradle'):
                    size=np.fromstring(geom.get('size'),sep=' ')
                    lo=max(pos[0]-size[0],-.034);hi=pos[0]+size[0]
                    if hi<=lo:continue
                    pos[0]=(hi+lo)/2;size[0]=(hi-lo)/2;geom.set('size',fmt(size))
                geom.set('pos',fmt(pos-pivot));yaw.append(geom)
        visual(yaw,side+'_fixed_roll_cradle',cradle,pivot)
        plate=box((24,22,3),(-22,y,52.9))
        post=cyl(4.,8.,(-25,y,53.5))
        coupler=union(plate,post)
        if a.manufacturer_yaw_layout:
            flange=cyl(8.,2.,(-25,y,60.))
            for dx,dy in ((6,0),(0,6),(-6,0),(0,-6)):
                flange=flange.cut(cyl(1.1,3.,(-25+dx,y+dy,59.5)))
            coupler=union(coupler,flange)
            if not coupler.isValid() or len(coupler.Solids())!=1:
                raise ValueError('output coupler must be a connected valid solid')
            ET.SubElement(yaw,'geom',name='col_'+side+'_yaw_flange',type='cylinder',size='.008 .001',
                          pos=fmt(np.array([-.025,y/1000,.061])-pivot),**{'class':'collision'})
        moving_records.append(record_shape(side+'_yaw_coupler',coupler))
        visual(yaw,side+'_yaw_coupler',coupler,pivot)
        collision_box(yaw,side+'_yaw_coupler_plate',(24,22,3),(-22,y,52.9),pivot)
        ET.SubElement(yaw,'geom',name='col_'+side+'_yaw_coupler_post',type='cylinder',size='.004 .004',
                      pos=fmt(np.array([-.025,y/1000,.0575])-pivot),**{'class':'collision'})
        if a.manufacturer_yaw_layout:
            # STEP front face z=6.5 maps to robot z=62; no rear idler.
            # Mass distribution is still a uniform-density approximation, not
            # the unconfirmed reference-point tensor from the vendor PDF.
            case_size,case_center=(34,20,23),(-32.5,y,76.5)
            case=box(case_size,case_center)
            horn=cyl(8.,3.,(-25,y,62.))
            horn_mass=.018*horn.Volume()/(horn.Volume()+case.Volume())
            case_mass=.018-horn_mass
            horn_name=side+'_yaw_motor_horn'
            moving_records.append(record_shape(horn_name,horn,horn_mass))
            visual(yaw,horn_name,horn,pivot)
            ET.SubElement(yaw,'geom',name='col_'+horn_name,type='cylinder',size='.008 .0015',
                          pos=fmt(np.array([-.025,y/1000,.0635])-pivot),**{'class':'collision'})
        else:
            case_size,case_center=(20,34,26),(-25,y,75)
            case=box(case_size,case_center);case_mass=.018
        name=side+'_yaw_motor_case';records[name]=record_shape(name,case,case_mass)
        visual(base,name,case);collision_box(base,name,case_size,case_center)
        # Internal rear upright connects the existing rear support rail to a
        # top shelf. Case and screw interfaces are still provisional envelopes.
        shelf=box((47.5,36,3),(-38.25,y,89.5))
        upright=box((3,20,40.2),(-60,y,70))
        support=union(shelf,upright)
        name=side+'_yaw_fixed_support';records[name]=record_shape(name,support)
        visual(base,name,support)
        collision_box(base,name+'_shelf',(47.5,36,3),(-38.25,y,89.5))
        collision_box(base,name+'_upright',(3,20,40.2),(-60,y,70))
        new=aggregate(moving_records,pivot);stored[side+'_hip_yaw']=new;set_inertial(yaw,new)
        new_parts.extend(moving_records);yaw_bodies.append(yaw)
        ET.SubElement(root.find('actuator'),'motor',name=side+'_hip_yaw_motor',joint=side+'_hip_yaw',gear='1',
                      ctrllimited='true',ctrlrange='-.26 .26',forcelimited='true',forcerange='-.26 .26')
    # Preserve disabled parent filtering and the original contact parameters.
    # Do not add pair defaults that would override the geom friction/solver law.
    new_base=aggregate(list(records.values()));stored['base']=new_base;set_inertial(base,new_base)
    for key in root.findall('.//key'):
        old=np.fromstring(key.get('qpos'),sep=' ')
        key.set('qpos',fmt(np.r_[old[:7],0.,old[7:12],0.,old[12:17]]))
    ET.indent(root);ET.ElementTree(root).write(a.out/'models/scene.xml',encoding='unicode')
    robot=json.loads((a.baseline/'robot.json').read_text());robot['revision']='r7-yaw-candidate-unverified-support'
    if a.manufacturer_yaw_layout:
        robot['revision']='r8-yaw-offset-flange-provisional-mount'
        root.set('model',robot['revision'])
        ET.ElementTree(root).write(a.out/'models/scene.xml',encoding='unicode')
    robot['motor']['quantity']+=2;robot['joint_limits_rad']['hip_yaw']=[-.09,.09]
    robot['hip_yaw_candidate']={'axis_base_m':{'left':[-.025,.022,.062],'right':[-.025,-.022,.062]},
                                'TTL_shift_z_m':.012,'manufacturing_release':False}
    (a.out/'robot.json').write_text(json.dumps(robot,indent=2)+'\n')
    (a.out/'models/inertials.json').write_text(json.dumps(stored,indent=2)+'\n')
    old_map=json.loads((a.baseline/'models/joint_map.json').read_text());joint_map=[]
    for side in ('left','right'):
        pivot=np.array(robot['hip_yaw_candidate']['axis_base_m'][side])
        joint_map.append({'name':side+'_hip_yaw','axis':[0,0,1],'origin_m':pivot.tolist(),
                          'servo':robot['motor']['name'],'torque_cap_Nm':.26,'supply_V':5})
        leg=copy.deepcopy([j for j in old_map if j['name'].startswith(side+'_')])
        leg[0]['origin_m']=(np.array(leg[0]['origin_m'])-pivot).tolist()
        joint_map.extend(leg)
    for i,item in enumerate(joint_map):item.update(index=i,suggested_bus_id=i+1)
    (a.out/'models/joint_map.json').write_text(json.dumps(joint_map,indent=2)+'\n')
    report={'scope':__doc__,'base_before':old_base,'base_after':new_base,'new_yaw_link_parts':new_parts,
            'fixed_base_parts':list(records.values()),'parent_collision_filtering':'disabled',
            'total_mass_kg':sum(r['mass_kg'] for r in stored.values()),
            'manufacturer_yaw_layout':a.manufacturer_yaw_layout,
            'yaw_mass_approximation':'uniform envelope density; total 18 g each; split rotating horn by volume' if a.manufacturer_yaw_layout else 'uniform box',
            'rear_idler_installed':False if a.manufacturer_yaw_layout else None,
            'not_verified':([] if a.manufacturer_yaw_layout else ['manufacturer shaft/horn offset'])+['fasteners and actual bearings','support strength and stiffness',
                            'swept CAD clearance with new supports','actuator identification','maneuver acceptance'],
            'source_sha256':{str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in
                             [Path(__file__),a.baseline/'models/scene.xml',a.baseline/'BATTERY_MOUNT_PATCH.json',d/'cad/r4_geometry.py',d/'cad/build.py',d/'robot.json',concept_path,a.mount/'battery_tray.step']}}
    (a.out/'CANDIDATE.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'mass_kg':report['total_mass_kg'],'parent_collision_filtering':'disabled'}))


if __name__=='__main__':main()
