#!/usr/bin/env python3
"""Assemble a separate r9 development plant from CAD-derived component inertias."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET
import numpy as np
import mujoco
from screen_fast_turn_clearance import candidate_tree


def aggregate(records, origin=(0,0,0)):
    mass = sum(r['mass_kg'] for r in records)
    com = sum(r['mass_kg']*np.array(r['com_base_m']) for r in records)/mass
    inertia = np.zeros((3,3))
    for r in records:
        delta = np.array(r['com_base_m'])-com
        inertia += np.array(r['inertia_com_kg_m2']) + r['mass_kg']*(delta@delta*np.eye(3)-np.outer(delta,delta))
    return {'mass_kg': mass, 'com_m': (com-np.array(origin)).tolist(), 'inertia_kg_m2': inertia.tolist()}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    if a.out.exists(): p.error('new output required')
    old=Path('assets/r8_yaw_offset_flange_v1')
    package=Path('validation/fast_turn_development_v1/packaging_cad_v2')
    feet=Path('validation/fast_turn_development_v1/feet_cad_v1')
    fixed=json.loads((package/'report.json').read_text())['properties']
    foot=json.loads((feet/'report.json').read_text())['properties']
    previous=json.loads((old/'CANDIDATE.json').read_text())
    root=candidate_tree(old/'models/scene.xml',4,-5,86,4,30,True,True,True)
    root.set('model','r9-fast-turn-development')
    base=root.find('.//body[@name="base"]')
    asset=root.find('asset')
    inertials=json.loads((old/'models/inertials.json').read_text())
    fmt=lambda values:' '.join(f'{v:.15g}' for v in values)
    def inertia(body, record):
        prior=body.find('inertial')
        if prior is not None:body.remove(prior)
        I=np.array(record['inertia_kg_m2'])
        ET.SubElement(body,'inertial',mass=str(record['mass_kg']),pos=fmt(record['com_m']),
                      fullinertia=fmt([I[0,0],I[1,1],I[2,2],I[0,1],I[0,2],I[1,2]]))
        inertials[body.get('name')]=record
    shutil.copytree(old/'models',a.out/'models')
    (a.out/'cad').mkdir()
    def visual(body,name,folder,origin=(0,0,0)):
        for geom in list(body.findall('geom')):
            if geom.get('name')=='vis_'+name or (name=='battery_tray' and geom.get('name')=='battery_tray_visual'):
                body.remove(geom)
        mesh=asset.find('mesh[@name="'+name+'_mesh"]')
        if mesh is None:mesh=ET.SubElement(asset,'mesh',name=name+'_mesh')
        mesh.set('file',name+'.stl');mesh.set('scale','.001 .001 .001')
        shutil.copyfile(folder/(name+'.stl'),a.out/'models/meshes'/(name+'.stl'))
        shutil.copyfile(folder/(name+'.step'),a.out/'cad'/(name+'.step'))
        ET.SubElement(body,'geom',name='vis_'+name,type='mesh',mesh=name+'_mesh',
                      pos=fmt(-np.array(origin)),rgba='.65 .7 .7 1',contype='0',conaffinity='0',mass='0',group='2')
    # Remove superseded battery visuals, including the former rear screw envelopes.
    for g in list(base.findall('geom')):
        if 'battery' in g.get('name','') and g.get('contype')=='0':base.remove(g)
    fixed_records=[]
    for name,r in fixed.items():
        if name.endswith('_yaw_coupler'):continue
        r=copy.deepcopy(r)
        if name.endswith('_screw_envelope'):
            # Explicit provisional 0.30 g per M2 screw, uniform envelope inertia.
            scale=.00030/r['mass_kg']
            r['mass_kg']=.00030
            r['inertia_com_kg_m2']=(np.array(r['inertia_com_kg_m2'])*scale).tolist()
        fixed_records.append(r)
        visual(base,name,package)
    inertia(base,aggregate(fixed_records))
    # These collision shapes follow the revised shelf, converter and coupler CAD.
    converter=base.find('geom[@name="col_dedicated_5V_converter_0"]')
    converter.set('pos','-.040 0 .073')
    for side,sign in [('left',1),('right',-1)]:
        pivot=np.array([-.005,sign*.026,.062])
        yaw=root.find('.//body[@name="'+side+'_hip_yaw"]')
        yaw.find('joint').set('range',fmt(np.deg2rad([-15,15])))
        shelf=base.find('geom[@name="col_'+side+'_yaw_fixed_support_shelf"]')
        shelf.set('size','.03575 .018 .0015');shelf.set('pos',fmt([-.02575,sign*.026,.0895]))
        upright=base.find('geom[@name="col_'+side+'_yaw_fixed_support_upright"]')
        upright.set('pos',fmt([-.06,sign*.026,.07]))
        plate=yaw.find('geom[@name="col_'+side+'_yaw_coupler_plate"]')
        plate.set('size','.0175 .011 .0015');plate.set('pos',fmt(np.array([-.0165,sign*.026,.0529])-pivot))
        moving=[]
        for record in previous['new_yaw_link_parts']:
            if not record['part'].startswith(side+'_'):continue
            r=copy.deepcopy(record)
            if r['part'].endswith('yaw_coupler'):
                r=copy.deepcopy(fixed[r['part']])
            else:
                shift=[.020 if r['part'].endswith('motor_horn') else 0,sign*.004,0]
                r['com_base_m']=(np.array(r['com_base_m'])+shift).tolist()
            moving.append(r)
        inertia(yaw,aggregate(moving,pivot))
        visual(yaw,side+'_yaw_coupler',package,pivot)
        foot_records=[]
        ankle=root.find('.//body[@name="'+side+'_ankle_roll"]')
        for suffix in ['foot_yoke','boot_shell','sole_TPU']:
            name=side+'_'+suffix
            r=copy.deepcopy(foot[name]);r['com_base_m']=r.pop('com_link_m');foot_records.append(r)
            visual(ankle,name,feet)
        inertia(ankle,aggregate(foot_records))
        site=ankle.find('site');site.set('pos',fmt([.004,sign*.006,-.022]));site.set('size','.043 .024 .0005')
    root.find('compiler').set('meshdir','meshes')
    ET.indent(root)
    ET.ElementTree(root).write(a.out/'models/scene.xml',encoding='unicode')
    (a.out/'models/inertials.json').write_text(json.dumps(inertials,indent=2)+'\n')
    robot=json.loads((old/'robot.json').read_text())
    robot['revision']='r9-fast-turn-development'
    robot['kinematics'].update(hip_half_spacing_mm=26,foot_length_mm=86,foot_width_mm=48,foot_center_x_mm=4,foot_outset_y_mm=6)
    robot['hip_yaw_candidate']['axis_base_m']={'left':[-.005,.026,.062],'right':[-.005,-.026,.062]}
    robot['hip_yaw_candidate']['limits_rad']=np.deg2rad([-15,15]).tolist()
    (a.out/'robot.json').write_text(json.dumps(robot,indent=2)+'\n')
    reference=a.out/'reference'
    shutil.copytree(Path('design/teleop_reference/src'),reference/'src')
    (reference/'models').mkdir()
    shutil.copyfile(Path('design/teleop_reference/models/inertials.json'),reference/'models/inertials.json')
    (reference/'robot.json').write_text(json.dumps(robot,indent=2)+'\n')
    mapping=json.loads((old/'models/joint_map.json').read_text())
    for joint in mapping:
        element=root.find('.//body[@name="'+joint['name']+'"]')
        joint['origin_m']=np.fromstring(element.get('pos','0 0 0'),sep=' ').tolist()
    (a.out/'models/joint_map.json').write_text(json.dumps(mapping,indent=2)+'\n')
    model=mujoco.MjModel.from_xml_path(str((a.out/'models/scene.xml').resolve()))
    data=mujoco.MjData(model);mujoco.mj_resetDataKeyframe(model,data,0);mujoco.mj_forward(model,data)
    bad=[{'pair':[model.geom(c.geom1).name,model.geom(c.geom2).name],'distance_m':float(c.dist)}
         for c in data.contact if c.dist < -1e-8 and 'floor' not in [model.geom(c.geom1).name,model.geom(c.geom2).name]]
    report={'scope':__doc__,'mass_kg':float(model.body_mass.sum()),'home_penetrations':bad,
            'screw_mass_assumption_kg_each':.00030,
            'not_verified':['full CAD swept clearance','support interfaces and strength',
                            'motor identification','90 degree turning performance'],
            'source_sha256':{str(path):hashlib.sha256(path.read_bytes()).hexdigest()
                              for path in [Path(__file__),Path('screen_fast_turn_clearance.py'),package/'report.json',feet/'report.json',old/'models/scene.xml']}}
    (a.out/'DEVELOPMENT.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))


if __name__=='__main__':main()
