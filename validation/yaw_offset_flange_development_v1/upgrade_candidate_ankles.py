#!/usr/bin/env python3
"""Compare XC330 ankle-pitch motors, including mass, inertia and speed changes."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import xml.etree.ElementTree as ET
import numpy as np

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--design',type=Path,default=Path('assets/r7_yaw_candidate_v1'))
    p.add_argument('--cad-design',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--flip-knee-cases',action='store_true',help='also compare knee cases rotated 180 degrees about their existing output axes')
    p.add_argument('--knee-case-angle-deg',type=int,choices=[0,90,180],default=0)
    a=p.parse_args()
    if a.out.exists():p.error('new output required')
    if a.flip_knee_cases and a.knee_case_angle_deg:p.error('use one knee orientation option')
    knee_angle=180 if a.flip_knee_cases else a.knee_case_angle_deg
    d=a.cad_design.resolve();sys.path[:0]=[str(d/'cad'),str(d/'src')]
    from build import build
    from r4_geometry import mass_properties
    parts=build()
    robot=json.loads((a.design/'robot.json').read_text())
    if 'ankle_pitch' in robot['motor_overrides']['joint_types']:raise ValueError('already upgraded')
    inertials=json.loads((a.design/'models/inertials.json').read_text())
    tree=ET.parse(a.design/'models/scene.xml');root=tree.getroot()
    changes=[];geometry_updates=[]
    def aggregate(group):
        values=[mass_properties(p) for p in group]
        mass=sum(m for m,r,I in values);com=sum(m*r for m,r,I in values)/mass
        inertia=sum(I+m*((r-com)@(r-com)*np.eye(3)-np.outer(r-com,r-com)) for m,r,I in values)
        return {'mass_kg':mass,'com_m':com.tolist(),'inertia_kg_m2':inertia.tolist()}
    fmt=lambda values:' '.join(f'{v:.15g}' for v in values)
    for side in ('left','right'):
        name=side+'_ankle_pitch_motor';part=next(p for p in parts if p.name==name)
        group=[p for p in parts if p.link==part.link and p.role!='visual']
        old=aggregate(group)
        for key,value in old.items():
            if not np.allclose(value,inertials[part.link][key],rtol=1e-9,atol=1e-12):raise ValueError('CAD/link inertia mismatch')
        old_mass=part.mass;part.mass=robot['motor_overrides']['mass_kg']
        new=aggregate(group);inertials[part.link]=new
        body=root.find(f".//body[@name='{part.link}']");body.remove(body.find('inertial'))
        I=np.array(new['inertia_kg_m2'])
        ET.SubElement(body,'inertial',mass=str(new['mass_kg']),pos=fmt(new['com_m']),
                      fullinertia=fmt([I[0,0],I[1,1],I[2,2],I[0,1],I[0,2],I[1,2]]))
        cap=robot['motor_overrides']['simulation_torque_cap_Nm']
        actuator=root.find(f"actuator/motor[@name='{name}']")
        actuator.set('ctrlrange',fmt([-cap,cap]));actuator.set('forcerange',fmt([-cap,cap]))
        changes.append({'part':name,'link':part.link,'old_motor_mass_kg':old_mass,'new_motor_mass_kg':part.mass,
                        'old_inertial':old,'new_inertial':new})
    robot['motor_overrides']['joint_types'].append('ankle_pitch')
    robot['motor_overrides']['quantity']+=2;robot['motor']['quantity']-=2
    robot['revision']+='-xc-ankle-pitch';root.set('model',robot['revision'])
    if knee_angle:
        for side in ('left','right'):
            name=side+'_knee_motor';part=next(p for p in parts if p.name==name)
            group=[p for p in parts if p.link==part.link and p.role!='visual']
            old=aggregate(group)
            for key,value in old.items():
                if not np.allclose(value,inertials[part.link][key],rtol=1e-9,atol=1e-12):raise ValueError('knee case CAD/link mismatch')
            length=robot['kinematics']['thigh_mm']
            part.shape=part.shape.rotate((0,0,-length),(0,1,-length),knee_angle)
            new=aggregate(group);inertials[part.link]=new
            body=root.find(f".//body[@name='{part.link}']");body.remove(body.find('inertial'))
            I=np.array(new['inertia_kg_m2'])
            ET.SubElement(body,'inertial',mass=str(new['mass_kg']),pos=fmt(new['com_m']),
                          fullinertia=fmt([I[0,0],I[1,1],I[2,2],I[0,1],I[0,2],I[1,2]]))
            geom=body.find(f"geom[@name='col_{name}_0']")
            angle=np.deg2rad(knee_angle);c,s=round(np.cos(angle)),round(np.sin(angle))
            rotation=np.array([[c,0,s],[0,1,0],[-s,0,c]])
            pivot=np.array([0,0,-length/1000])
            pos=np.fromstring(geom.get('pos'),sep=' ')
            geom.set('pos',fmt(pivot+rotation@(pos-pivot)))
            geom.set('size',fmt(abs(rotation)@np.fromstring(geom.get('size'),sep=' ')))
            changes.append({'part':name,'link':part.link,'rotation_about_output_axis_deg':knee_angle,
                            'old_inertial':old,'new_inertial':new})
            geometry_updates.append((name,part.shape))
        robot['revision']+=f'-knee-cases-{knee_angle}deg';root.set('model',robot['revision'])
        robot['knee_case_orientation']=f'{knee_angle} degrees about existing knee motor axes; joint positions unchanged'
    shutil.copytree(a.design,a.out)
    if geometry_updates:
        import cadquery as cq
        for name,shape in geometry_updates:
            cq.exporters.export(shape,str(a.out/'models/meshes'/(name+'.stl')),tolerance=.09,angularTolerance=.15)
            cq.exporters.export(shape,str(a.out/'cad'/(name+'.step')))
    (a.out/'FROZEN_FILES.json').unlink(missing_ok=True)
    ET.indent(root);tree.write(a.out/'models/scene.xml',encoding='unicode')
    (a.out/'robot.json').write_text(json.dumps(robot,indent=2)+'\n')
    (a.out/'models/inertials.json').write_text(json.dumps(inertials,indent=2)+'\n')
    mapping=json.loads((a.out/'models/joint_map.json').read_text())
    for item in mapping:
        if item['name'].endswith('ankle_pitch'):
            item.update(servo=robot['motor_overrides']['name'],torque_cap_Nm=cap)
    (a.out/'models/joint_map.json').write_text(json.dumps(mapping,indent=2)+'\n')
    report={'scope':__doc__,'source_model':str(a.design),'changes':changes,
            'motor_specification':robot['motor_overrides'],
            'specification_source':'https://emanual.robotis.com/docs/en/dxl/x/xc330-m288/',
            'simulation_cap_is_not_continuous_rating':True,'uniform_case_inertia_approximation':True,
            'source_sha256':{str(path):sha(path) for path in [Path(__file__),a.design/'models/scene.xml',a.design/'robot.json',d/'cad/build.py',d/'cad/r4_geometry.py']}}
    (a.out/'ANKLE_UPGRADE.json').write_text(json.dumps(report,indent=2)+'\n')
    candidate=json.loads((a.out/'CANDIDATE.json').read_text())
    candidate['total_mass_kg']=sum(r['mass_kg'] for r in inertials.values())
    candidate['subsequent_actuator_upgrade']='ANKLE_UPGRADE.json'
    (a.out/'CANDIDATE.json').write_text(json.dumps(candidate,indent=2)+'\n')
    with (a.out/'README.md').open('a') as f:
        f.write('\n## Actuator comparison variant\n\n'
                'Both ankle-pitch motors use the XC330 specification, including mass, inertia, '
                'speed and torque limits. See `ANKLE_UPGRADE.json` for provenance. '
                'The simulation torque cap is not a manufacturer continuous rating.\n\n'
                f'Knee case rotation about the existing output axes: {knee_angle} degrees. '
                'Joint axes and leg lengths are unchanged. Rotated cases are packaging '
                'experiments, not validated mounting designs. No walking acceptance is claimed.\n')
    files={str(path.relative_to(a.out)):sha(path) for path in sorted(a.out.rglob('*')) if path.is_file()}
    (a.out/'FROZEN_FILES.json').write_text(json.dumps(files,indent=2)+'\n')
    print(json.dumps({'mass_kg':candidate['total_mass_kg'],'ankle_cap_Nm':cap,'ankle_no_load_rpm':robot['motor_overrides']['no_load_speed_rpm']}))


if __name__=='__main__':main()
