"""Side-loaded square-nut retention candidate; no strength or assembly release."""
import argparse,hashlib,json,math
from pathlib import Path
import cadquery as cq
ROOT=Path(__file__).resolve().parents[3]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--slot-width-mm',type=float,default=6.4)
a=p.parse_args()
if not 6.2<=a.slot_width_mm<=6.4:p.error('Slot width must be 6.2 to 6.4 mm')
a.out.mkdir(parents=True,exist_ok=False)
source=ROOT/'validation/rear_joint_assembly_development_v1/rear_joint_socket_double_v1'
base=ROOT/'software/sim/mujoco/assets/r9_fast_turn_v1/cad'
body=cq.importers.importStep(str(source/'body_shroud.step')).val();old_volume=body.Volume()
plan={'scope':__doc__,'nut':{'candidate':'Accu HFSN-M3-A4, DIN562','source':'https://www.accu.co.uk/flat-square-nuts/21333-HFSN-M3-A4','width_max_mm':5.5,'width_min_mm':5.1,'thickness_max_mm':1.8,'thickness_min_mm':1.4,'thread':'M3x0.5','strength_class':'not qualified'},
      'pocket':{'width_z_mm':a.slot_width_mm,'thickness_x_mm':2.4,'surface_tolerance_mm':.2,'nut_back_x_mm':-55.7,'slot_back_x_mm':-55.9,'slot_front_x_mm':-53.5},
      'criteria':{'intersection_mm3':.01,'minimum_total_fit_clearance_mm':.1,'rotation_stop_before_deg':45},
      'source_sha256':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [source/'body_shroud.step',source/'rear_structural_plate.step']},
      'limitations':['square envelope ignores corner radii','nut thread strength/preload not verified','retention under tightening torque not verified','insertion starts inside body; human/tool approach not yet verified','side-open pocket does not prevent nut escape before bolt insertion']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
def box(x,y,z,dx,dy,dz):return cq.Solid.makeBox(dx,dy,dz,cq.Vector(x,y,z))
def cyl(r,length,x,y,z):return cq.Solid.makeCylinder(r,length,cq.Vector(x,y,z),cq.Vector(1,0,0))
centers=[(sign*57,z,sign) for sign in [-1,1] for z in [8,120]]
for y,z,sign in centers:
    housing=box(-56.3,y-4.6,z-4.6,4,9.2,9.2)
    body=body.fuse(housing)
    # Seat one washer against the original boss front; reserve radial tolerance.
    body=body.cut(cyl(3.8,.7,-56.3,y,z))
    # Slot opens toward the body center; outer end retains nut positioning.
    slot_y=y-20 if sign>0 else y-3.1
    body=body.cut(box(-55.9,slot_y,z-a.slot_width_mm/2,2.4,23.1,a.slot_width_mm))
    body=body.cut(cyl(1.7,12,-63,y,z))
body=body.clean();assert body.isValid() and len(body.Solids())==1
cq.exporters.export(body,str(a.out/'body_shroud.step'))
parts={'body':body,'plate':cq.importers.importStep(str(source/'rear_structural_plate.step')).val()}
for name in ['battery_tray','battery_2S_reservation','dedicated_5V_converter','TTL_interface','left_yaw_coupler','right_yaw_coupler','left_yaw_motor_case','right_yaw_motor_case']:
    parts[name]=cq.importers.importStep(str(base/(name+'.step'))).val()
for side in ['left','right']:
    parts[side+'_support']=cq.importers.importStep(str(ROOT/f'validation/inset_yaw_assembly_development_v1/yaw_inset_mount_v1/{side}_yaw_fixed_support.step')).val()
checks=[]
for i,(y,z,sign) in enumerate(centers):
    nut=box(-55.7,y-2.75,z-2.75,1.8,5.5,5.5).cut(cyl(1.25,1.8,-55.7,y,z))
    path_y=y-20-2.75 if sign>0 else y-2.75
    # This solid contains the nut for every position of the straight 20 mm slide.
    sweep=box(-55.7,path_y,z-2.75,1.8,25.5,5.5)
    bolt=cyl(1.5,16,-64.7,y,z).fuse(cyl(2.75,3,-67.7,y,z))
    washer=cyl(3.5,.5,-56.2,y,z).cut(cyl(1.6,.5,-56.2,y,z))
    for name,shape in [('nut',nut),('insertion_sweep',sweep),('bolt',bolt),('inner_washer',washer)]:
        cq.exporters.export(shape,str(a.out/f'corner_{i}_{name}.step'))
        clashes=[]
        for part,solid in parts.items():
            if shape.distance(solid)<1e-6:
                volume=float(shape.intersect(solid).Volume())
                if volume>.01:clashes.append({'part':part,'volume_mm3':volume})
        checks.append({'corner':i,'shape':name,'clashes':clashes})
width_min=a.slot_width_mm-.4;width_max=a.slot_width_mm+.4;thickness_min=2.4-.4
max_nut=5.5;min_nut=5.1
rotation_stop=45-math.degrees(math.acos(width_max/(math.sqrt(2)*min_nut)))
fit={'width_clearance_worst_mm':width_min-max_nut,'thickness_clearance_worst_mm':thickness_min-1.8,
     'square_envelope_rotation_stop_worst_deg':rotation_stop,'square_diagonal_min_mm':math.sqrt(2)*min_nut,
     'passed':bool(width_min-max_nut>=.1 and thickness_min-1.8>=.1 and rotation_stop<45)}
report={'scope':__doc__,'body_added_mass_kg_at_1270kg_m3':(body.Volume()-old_volume)*1.27e-6,'fit':fit,'checks':checks,
        'interference_count':sum(len(r['clashes']) for r in checks),'manufacturing_release':False,'joint_strength_verified':False}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='checks'}))
