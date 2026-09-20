"""Generate the editable prototype specification without changing frozen r9 data."""
import copy
import csv
import hashlib
import json
from pathlib import Path
import sys
import mujoco
import numpy as np
from result_bundle import ROOT

SIM=ROOT/'software/sim/mujoco'
sys.path.insert(0,str(SIM))
from stackchan_rl.residual import runtime_xml


def build():
    model_dir=SIM/'assets/r9_fast_turn_v1'
    scene=model_dir/'models/scene.xml'
    model=mujoco.MjModel.from_xml_string(runtime_xml(scene))
    robot=json.loads((model_dir/'robot.json').read_text())
    mapping=json.loads((model_dir/'models/joint_map.json').read_text())
    out=ROOT/'board/mechanical/prototype';out.mkdir(exist_ok=True)
    joints=[]
    for record in mapping:
        name=record['name'];joint=model.joint(name);aid=model.actuator(name+'_motor').id
        joint_type=name.split('_',1)[1]
        robot['joint_limits_rad'][joint_type]=joint.range.tolist()
        joints.append({'name':name,'index':record['index'],'bus_id':record['suggested_bus_id'],
                       'motor':record['servo'],'axis_joint_frame':joint.axis.tolist(),
                       'joint_position_body_m':joint.pos.tolist(),'body':model.body(int(joint.bodyid[0])).name,
                       'zero_rad':0.,'positive_direction':'right-hand rule about axis_joint_frame',
                       'mechanical_range_rad':joint.range.tolist(),
                       'reference_range_rad':[-.245,.245] if joint_type=='hip_yaw' else joint.range.tolist(),
                       'target_margin_rad':.015,
                       'simulation_torque_limit_Nm':float(model.actuator_ctrlrange[aid,1]),
                       'supply_V':record['supply_V'],
                       'encoder_mapping':{'counts_per_revolution':4096,'design_zero_count':2048,
                                          'design_sign':1,'calibrated_zero_count':None,'calibrated_sign':None,
                                          'status':'assembly convention; actual calibration required before enabling hardware'}})
    robot['revision']='prototype-r9-spec-v1'
    robot['scope'].update(arms=False,yaw_actuators=True,
                         walking_controller_status='r9 finite turn simulation baseline; no hardware validation',
                         hardware_control_enabled=False)
    robot['gait']={'source':'software/sim/mujoco/fast_turn_reference.py',
                   'finite_turn':{'period_s':.4,'shift_fraction':.45,'initial_inset_mm':25.5,
                                  'steady_inset_mm':25.5,'command_rate_deg_s':40.,'reference_goal_deg':91.5},
                   'note':'Legacy robot.json gait is not the runtime gait. Direction changes the signs and first support foot.'}
    placement=json.loads((ROOT/'validation/fast_turn_development_v1/packaging_cad_v5/report.json').read_text())['properties']
    battery_center=(np.array(placement['battery_2S_reservation']['com_base_m'])*1000).tolist()
    robot['battery_envelope']['center_base_mm']=battery_center
    robot['battery_mount']['center_base_mm']=battery_center
    robot['component_com_base_m']={name:placement[name]['com_base_m'] for name in ['battery_2S_reservation','dedicated_5V_converter','TTL_interface','Tab5']}
    robot['source']={'path':str(scene.relative_to(ROOT)),'sha256':hashlib.sha256(scene.read_bytes()).hexdigest(),
                     'kind':'frozen simulation baseline, not a measured robot'}
    frames={'handedness':'right','length_unit':'m','angle_unit':'rad','mass_unit':'kg',
            'world':{'x':'initial forward','y':'initial left','z':'up'},
            'base':'MuJoCo base body frame; at initial heading x forward, y left, z up',
            'joint_zero':'MJCF hinge reference (q=0); not necessarily inside its operational range or a standing pose',
            'joint_axis':'axis in joint body local frame; positive right-hand rotation',
            'encoder_formula':'q_rad = calibrated_sign * (raw_count - calibrated_zero_count) * 2*pi/4096',
            'hardware_calibration_required':True}
    links=[{'body':model.body(i).name,'mass_kg':float(model.body_mass[i]),
            'com_body_m':model.body_ipos[i].tolist(),'principal_inertia_kg_m2':model.body_inertia[i].tolist(),
            'principal_frame_quaternion_wxyz':model.body_iquat[i].tolist(),'status':'derived'} for i in range(1,model.nbody)]
    total=sum(x['mass_kg'] for x in links)
    bom=[
        ('XL330-M288-T',6,.018,'candidate','hip yaw, hip pitch, ankle roll; each side'),
        ('XC330-M288-T',6,.023,'candidate','hip roll, knee, ankle pitch; each side'),
        ('Tab5',1,.1184,'datasheet-derived baseline','landscape face; mounting thread depth to verify'),
        ('Battery reservation',1,.103,'assumed','K145 envelope candidate; electrical compatibility unresolved'),
        ('5 V converter reservation',1,.020,'assumed','part number/rating unresolved; EPIC #6'),
        ('Communication interface reservation',1,.012,'assumed','part number/circuit unresolved; EPIC #7'),
        ('Harness and miscellaneous fasteners allowance',1,.025,'assumed','wire lengths, connector/fastener quantities unresolved; excludes dedicated two tray screws'),
        ('Battery strap reservation',1,.0012,'assumed','strap specification unresolved'),
        ('Dedicated battery screw reservation',2,.0003,'assumed','M2 envelope; length/engagement unresolved'),
    ]
    hardware_mass=sum(n*m for _,n,m,_,_ in bom)
    bom.append(('Printed structure and remaining CAD allocation',1,total-hardware_mass,'derived aggregate',
                'remainder after commercial/allowance allocation; includes body, cover, tray, supports, links and soles; not an independently measured mass'))
    with (out/'bom.csv').open('w',newline='') as f:
        writer=csv.writer(f,lineterminator="\n");writer.writerow(['item','quantity','unit_mass_kg','subtotal_mass_kg','status','notes'])
        writer.writerows((name,n,m,n*m,status,note) for name,n,m,status,note in bom)
    # Inventory geometry separately from the additive accounting to avoid counting
    # a servo case and its whole assembly mass twice.
    mesh_inventory=[{'mesh':p.name,'role':'geometry inventory, not an additional BOM mass'} for p in sorted((model_dir/'models/meshes').glob('*.stl'))]
    for name,data in [('robot.json',robot),('joints.json',joints),('frames.json',frames),
                      ('mass_budget.json',{'total_mass_kg':total,'status':'derived simulation allocation','links':links}),
                      ('geometry_inventory.json',mesh_inventory)]:
        (out/name).write_text(json.dumps(data,indent=2)+'\n')
    print(json.dumps({'joints':len(joints),'mass_kg':total,'output':str(out)}))


if __name__=='__main__':build()
