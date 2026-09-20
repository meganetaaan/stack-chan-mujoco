"""Export MJCF and URDF from the same kinematics, CAD and inertials.
No third-party robot mesh or learned policy is embedded.
"""
from __future__ import annotations
import json
import xml.etree.ElementTree as E
import numpy as np
from scipy.spatial.transform import Rotation
from .core import ROOT,PARAMS as P,KIN,JOINT_TYPES,JOINT_NAMES,SIDES,AXES,origins,motor_spec,sole_offset
from .planner import Planner
from .collision_proxies import proxies


def fmt(x):
    return ' '.join(f'{float(v):.12g}' for v in np.asarray(x).flatten())

def node(parent,tag,**attrs):
    return E.SubElement(parent,tag,{k:str(v) for k,v in attrs.items()})

def save(root,path):
    E.indent(root,space='  ')
    E.ElementTree(root).write(path,encoding='utf-8',xml_declaration=True)

def main():
    comps=json.loads((ROOT/'models/components.json').read_text())['parts']
    inertia=json.loads((ROOT/'models/inertials.json').read_text())
    planner=Planner();home=np.r_[planner.b0[:3,3],1,0,0,0,planner.q0]
    model=E.Element('mujoco',model='Tab5_R5_A_landscape_cube_X330_10DOF')
    model.append(E.Comment('UNVALIDATED PHYSICS MODEL. Floating base; no weld, no root-force assistance.'))
    model.append(E.Comment('Reduced separated collision proxies: not exact CAD shell surfaces. See collision_proxies.py. No boot is represented as a solid convex hull.'))
    node(model,'compiler',angle='radian',meshdir='meshes',inertiafromgeom='false',autolimits='true')
    opt=node(model,'option',timestep=P['simulation']['timestep_s'],gravity=f"0 0 {-P['simulation']['gravity_m_s2']}",integrator='implicitfast',solver='Newton',iterations='50',cone='elliptic')
    # Keep normal parent-child collision filtering. Independent B-rep tests
    # include adjacent members, so this does not replace mechanism clearance.
    node(opt,'flag',filterparent='enable')
    visual=node(model,'visual');node(visual,'global',offwidth='1280',offheight='960')
    node(visual,'headlight',diffuse='.7 .7 .7',ambient='.3 .3 .3')
    node(model,'statistic',center='0 0 .15',extent='.55')
    defaults=node(model,'default')
    dj=node(defaults,'default',**{'class':'joint_defaults'})
    node(dj,'joint',type='hinge',limited='true',damping=P['motor']['joint_damping_Nm_s_rad'],frictionloss=P['motor']['joint_frictionloss_Nm'],armature=P['motor']['armature_kg_m2'])
    dc=node(defaults,'default',**{'class':'collision'})
    node(dc,'geom',contype='1',conaffinity='1',condim='3',group='3',rgba='.8 .3 .1 .35',friction=f"{P['simulation']['floor_friction']} .003 .0001",solref='.004 1',solimp='.95 .99 .001',margin='0',mass='0')
    asset=node(model,'asset')
    for p in comps:
        node(asset,'mesh',name=p['name']+'_mesh',file=p['mesh'].split('/')[-1],scale='.001 .001 .001')
    world=node(model,'worldbody')
    node(world,'light',pos='.3 -.4 1',dir='-.2 .2 -1',directional='true')
    node(world,'geom',name='floor',type='plane',size='2 2 .05',rgba='.89 .91 .92 1',friction=f"{P['simulation']['floor_friction']} .003 .0001",condim='3')
    base=node(world,'body',name='base',pos=fmt(planner.b0[:3,3]))
    node(base,'freejoint',name='floating_base')
    bodies={'base':base}
    joint_map=[]
    for side in SIDES:
        parent=base
        for j,jtype in enumerate(JOINT_TYPES):
            name=f'{side}_{jtype}';spec=motor_spec(name)
            body=node(parent,'body',name=name,pos=fmt(origins(side)[j]))
            node(body,'joint',name=name,axis=fmt(AXES[j]),range=fmt(P['joint_limits_rad'][jtype]),**{'class':'joint_defaults'})
            bodies[name]=body;parent=body
            joint_map.append(dict(name=name,index=len(joint_map),axis=AXES[j].tolist(),origin_m=origins(side)[j].tolist(),servo=spec['name'],torque_cap_Nm=spec['simulation_torque_cap_Nm'],supply_V=5,suggested_bus_id=len(joint_map)+1))
        node(parent,'site',name=side+'_sole',type='box',pos=fmt(sole_offset(side)),size=fmt([KIN['foot_length_mm']/2000,KIN['foot_width_mm']/2000,.0005]),rgba='0 .7 .5 .25',group='4')
    for name,b in bodies.items():
        ip=inertia[name];I=np.array(ip['inertia_kg_m2'])
        node(b,'inertial',mass=ip['mass_kg'],pos=fmt(ip['com_m']),fullinertia=fmt([I[0,0],I[1,1],I[2,2],I[0,1],I[0,2],I[1,2]]))
        for p in [p for p in comps if p['link']==name]:
            node(b,'geom',name='vis_'+p['name'],type='mesh',mesh=p['name']+'_mesh',rgba=fmt(p['color']+[1]),contype='0',conaffinity='0',group='2',mass='0')
            for i,c in enumerate(proxies(p)):
                a=dict(name='col_'+p['name']+'_'+str(i),type=c['type'],pos=fmt(c['pos']),size=fmt(c['size']))
                if 'axis' in c:a['zaxis']=fmt(c['axis'])
                node(b,'geom',**a,**{'class':'collision'})
    node(base,'site',name='imu',pos='0 0 .055',size='.003',rgba='0 1 1 1',group='4')
    sensors=node(model,'sensor');node(sensors,'gyro',name='imu_gyro',site='imu');node(sensors,'accelerometer',name='imu_accel',site='imu')
    node(sensors,'framequat',name='base_quat',objtype='body',objname='base')
    for name in JOINT_NAMES:
        node(sensors,'jointpos',name=name+'_pos',joint=name);node(sensors,'jointvel',name=name+'_vel',joint=name)
    actuators=node(model,'actuator')
    for name in JOINT_NAMES:
        cap=motor_spec(name)['simulation_torque_cap_Nm']
        node(actuators,'motor',name=name+'_motor',joint=name,gear='1',ctrllimited='true',ctrlrange=fmt([-cap,cap]),forcelimited='true',forcerange=fmt([-cap,cap]))
    keys=node(model,'keyframe');node(keys,'key',name='home',qpos=fmt(home))
    save(model,ROOT/'models/scene.xml')
    (ROOT/'models/joint_map.json').write_text(json.dumps(joint_map,indent=2))

    # Portable interchange URDF: root is base, not welded to a world link.
    # Multiple visuals/collisions per link preserve local mesh coordinates.
    urdf=E.Element('robot',name='Tab5_R5_A_landscape_cube_X330_10DOF')
    urdf.append(E.Comment('Interchange file only. MJCF is the primary physics model; no world fixed joint.'))
    for name,ip in inertia.items():
        l=node(urdf,'link',name=name);ii=node(l,'inertial');I=np.array(ip['inertia_kg_m2'])
        node(ii,'origin',xyz=fmt(ip['com_m']),rpy='0 0 0');node(ii,'mass',value=ip['mass_kg'])
        node(ii,'inertia',ixx=I[0,0],iyy=I[1,1],izz=I[2,2],ixy=I[0,1],ixz=I[0,2],iyz=I[1,2])
        for p in [p for p in comps if p['link']==name]:
            v=node(l,'visual',name=p['name']);node(v,'origin',xyz='0 0 0',rpy='0 0 0')
            node(node(v,'geometry'),'mesh',filename=p['mesh'],scale='.001 .001 .001')
            node(node(v,'material',name=p['name']+'_color'),'color',rgba=fmt(p['color']+[1]))
            for i,c in enumerate(proxies(p)):
                co=node(l,'collision',name=p['name']+str(i));rpy=np.zeros(3)
                if 'axis' in c:
                    axis=np.asarray(c['axis']);z=np.array([0,0,1.]);v=np.cross(z,axis)
                    if np.linalg.norm(v)>1e-10:rpy=Rotation.from_rotvec(v/np.linalg.norm(v)*np.arccos(z@axis)).as_euler('xyz')
                node(co,'origin',xyz=fmt(c['pos']),rpy=fmt(rpy));g=node(co,'geometry')
                if c['type']=='box':node(g,'box',size=fmt(np.array(c['size'])*2))
                else:node(g,'cylinder',radius=c['size'][0],length=c['size'][1]*2)
    for side in SIDES:
        parent='base'
        for j,jtype in enumerate(JOINT_TYPES):
            name=f'{side}_{jtype}';sp=motor_spec(name)
            jo=node(urdf,'joint',name=name,type='revolute');node(jo,'parent',link=parent);node(jo,'child',link=name)
            node(jo,'origin',xyz=fmt(origins(side)[j]),rpy='0 0 0');node(jo,'axis',xyz=fmt(AXES[j]))
            lo,hi=P['joint_limits_rad'][jtype];node(jo,'limit',lower=lo,upper=hi,effort=sp['simulation_torque_cap_Nm'],velocity=sp['no_load_speed_rpm']*np.pi/30)
            node(jo,'dynamics',damping=sp['joint_damping_Nm_s_rad'],friction=sp['joint_frictionloss_Nm']);parent=name
    save(urdf,ROOT/'models/tab5_r5.urdf')
    print('Exported MJCF, URDF, ten-axis joint map. XML written; MuJoCo compilation NOT executed here.')

if __name__=='__main__':main()
