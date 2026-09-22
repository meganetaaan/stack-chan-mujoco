"""Through-bolted rear plate/body candidate with inward-shifted corner axes."""
import argparse,hashlib,json
from pathlib import Path
import cadquery as cq
ROOT=Path(__file__).resolve().parents[3]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--inset-mm',type=float,default=2.);p.add_argument('--inner-washers',type=int,choices=[1,2],default=2);p.add_argument('--driver-model',choices=['local_socket','wera_2069_envelope'],default='wera_2069_envelope')
a=p.parse_args()
if not 0<=a.inset_mm<=3:p.error('Inset must be between 0 and 3 mm')
a.out.mkdir(parents=True,exist_ok=False)
base=ROOT/'software/sim/mujoco/assets/r9_fast_turn_v1/cad'
plate_path=ROOT/'validation/back_cover_development_v1/backplate_2mm_v3/rear_structural_plate.step'
body_path=base/'body_shroud.step'
body=cq.importers.importStep(str(body_path)).val();plate=cq.importers.importStep(str(plate_path)).val()
old_body_volume=body.Volume();old_plate_volume=plate.Volume()
plan={'scope':__doc__,'inset_mm':a.inset_mm,'corner_y_mm':59-a.inset_mm,'corner_z_mm':[8,120],
      'body_boss_back_x_mm':-62.2,'body_boss_front_x_mm':-56.2,'clearance_hole_diameter_mm':3.4,
      'bolt':'M3x16 nominal, class 8.8 candidate','washer':'OD7 / ID3.2 / thickness0.5 mm nominal',
      'nut':'circumscribed OD6.4 / thickness2.4 mm, thread placeholder',
      'inner_washer_count':a.inner_washers,'driver_model':a.driver_model,
      'tool_source':'https://hybris-media.wera.de/download/pdfgenerator-datasheets/en/05118126001.pdf',
      'wera_candidate':{'part_number':'05118126001','tip_mm':5.5,'blade_diameter_mm':7.8,'blade_length_mm':60,'handle_length_mm':97,'overall_max_diameter_mm':13,'cavity_depth_mm':8,'cavity_status':'assumed, not specified by source'},
      'tool':('OD8 local socket plus 25 mm access' if a.driver_model=='local_socket' else 'Wera 2069 05118126001 cylindrical blade and handle bounds')+'; cavity ID6.4 x8 mm assumed',
      'criteria':{'intersection_mm3':.01,'tool_residual_clearance_mm':.5,'surface_tolerance_each_mm':.2,'minimum_nominal_thread_projection_mm':1.},
      'source_sha256':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [body_path,plate_path]},
      'limitations':['nominal component envelopes','no screw preload or strength proof','neutral pose assembly subset','body boss root still unverified']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
def cyl(r,length,x,y,z):return cq.Solid.makeCylinder(r,length,cq.Vector(x,y,z),cq.Vector(1,0,0))
centers=[(sign*(59-a.inset_mm),z,sign*59) for sign in [-1,1] for z in [8,120]]
for y,z,old_y in centers:
    # Close the old pilot/plate holes before making the new through-hole.
    body=body.fuse(cyl(1.3,6,-62.2,old_y,z)).fuse(cyl(4.6,6,-62.2,y,z))
    plate=plate.fuse(cyl(1.7,2,-64.2,old_y,z))
    body=body.cut(cyl(1.7,8,-63,y,z));plate=plate.cut(cyl(1.7,4,-65,y,z))
body=body.clean();plate=plate.clean()
for name,shape in [('body_shroud',body),('rear_structural_plate',plate)]:
    assert shape.isValid() and len(shape.Solids())==1,(name,shape.isValid(),len(shape.Solids()))
    cq.exporters.export(shape,str(a.out/(name+'.step')))
assert abs(body.BoundingBox().ymin+64)<1e-6 and abs(body.BoundingBox().ymax-64)<1e-6
parts={'body_shroud':body,'rear_structural_plate':plate}
for name in ['Tab5','battery_2S_reservation','battery_tray','dedicated_5V_converter','TTL_interface','left_yaw_coupler','right_yaw_coupler','left_yaw_motor_case','right_yaw_motor_case']:
    parts[name]=cq.importers.importStep(str(base/(name+'.step'))).val()
support=ROOT/'validation/inset_yaw_assembly_development_v1/yaw_inset_mount_v1'
for side in ['left','right']:parts[side+'_support']=cq.importers.importStep(str(support/(side+'_yaw_fixed_support.step'))).val()
checks=[]
inner_thickness=.5*a.inner_washers
nut_back=-56.2+inner_thickness
nut_front=nut_back+2.4
stack=2+6+.5+inner_thickness+2.4
for index,(y,z,_) in enumerate(centers):
    shapes={'bolt':cyl(1.5,16,-64.7,y,z).fuse(cyl(2.75,3,-67.7,y,z)),
            'rear_washer':cyl(3.5,.5,-64.7,y,z).cut(cyl(1.6,.5,-64.7,y,z)),
            'nut':cyl(3.2,2.4,nut_back,y,z).cut(cyl(1.25,2.4,nut_back,y,z)),
            'nut_driver':cyl(4,27.4,nut_back,y,z).cut(cyl(3.2,8,nut_back,y,z)),
            'rear_key':cyl(1.5,25,-92.7,y,z)}
    if a.driver_model=='wera_2069_envelope':
        shapes['nut_driver']=cyl(3.9,60,nut_back,y,z).fuse(cyl(6.5,97,nut_back+60,y,z)).cut(cyl(3.2,8,nut_back,y,z))
    for j in range(a.inner_washers):
        x=-56.2+j*.5
        shapes[f'inner_washer_{j}']=cyl(3.5,.5,x,y,z).cut(cyl(1.6,.5,x,y,z))
    for name,shape in shapes.items():
        cq.exporters.export(shape,str(a.out/f'corner_{index}_{name}.step'))
        clashes=[];distances=[]
        for part,solid in parts.items():
            distance=float(shape.distance(solid))
            if distance<1e-6:
                overlap=float(shape.intersect(solid).Volume())
                if overlap>.01:clashes.append({'part':part,'volume_mm3':overlap})
            distances.append({'part':part,'distance_mm':distance})
        closest=min(distances,key=lambda r:r['distance_mm'])
        checks.append({'corner':index,'y_mm':y,'z_mm':z,'envelope':name,'clashes':clashes,'closest':closest,
                       'tool_clearance_passed':bool(closest['distance_mm']-.4>=.5) if name in ['nut_driver','rear_key'] else None})
report={'scope':__doc__,'body_added_volume_mm3':body.Volume()-old_body_volume,
        'body_added_mass_kg_at_1270kg_m3':(body.Volume()-old_body_volume)*1.27e-6,
        'plate_mass_change_kg_at_2700kg_m3':(plate.Volume()-old_plate_volume)*2.7e-6,
        'nominal_stack_mm':stack,'nominal_thread_projection_mm':16-stack,'checks':checks,
        'interference_count':sum(len(r['clashes']) for r in checks),
        'tool_clearance_failures':sum(r['tool_clearance_passed'] is False for r in checks),
        'manufacturing_release':False,'joint_strength_verified':False}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='checks'}))
