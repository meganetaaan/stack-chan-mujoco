"""Recessed M2 slide-lock screw and captive-nut boss for keyhole sole concept."""
import argparse,json,hashlib
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--rigid-seat',action='store_true');p.add_argument('--separate-seat',action='store_true');p.add_argument('--seat-radius-mm',type=float,default=2);a=p.parse_args();root=Path(__file__).resolve().parents[3];a.out.mkdir(parents=True,exist_ok=False)
seat=-19.9 if a.rigid_seat else -20.5
plan={'seat_radius_mm':a.seat_radius_mm,'separate_seat':a.separate_seat,'rigid_seat':a.rigid_seat,'scope':__doc__,'screw_envelope':{'diameter_mm':2,'length_mm':8,'head_diameter_mm':3.8,'head_height_mm':1.3,'seat_z_mm':seat},'nut_envelope_mm':[4,4,1.2],'nut_bottom_z_mm':-14.2,'criteria':{'single_valid_parts':True,'overlap_max_mm3':.01,'head_ground_recess_mm':.8 if a.rigid_seat else .2},'limitations':['Nominal envelopes only; M2x8 low-head screw not selected or tolerance-qualified.','TPU head bearing and PETG boss strength, preload, creep and nut print insertion remain unverified.','Sliding stops only after installation; friction not credited.']};(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');rows=[]
def cylinder(r,z,h,x,y):return cq.Solid.makeCylinder(r,h,cq.Vector(x,y,z))
for side,cy in [('left',6),('right',-6)]:
 paths={'sole':root/f'validation/keyhole_front18_v1/retention/{side}_sole_TPU.step','yoke':root/f'validation/keyhole_front18_v1/keyhole/{side}_foot_yoke.step','boot':root/f'validation/boot_low_head_candidate_v1/cad/{side}_boot_shell.step'};parts={k:cq.importers.importStep(str(f)).val() for k,f in paths.items()};x=35;y=cy
 sole=parts['sole'].cut(cylinder(a.seat_radius_mm+.2 if a.rigid_seat else 1.15,-22.01,3.02,x,y)).cut(cylinder(2.4,-22.01,seat+22.01,x,y)).clean()
 boss=cq.Solid.makeBox(8,8,4.41,cq.Vector(x-4,y-4,-16.01));yoke=parts['yoke'].fuse(boss).cut(cylinder(1.15,-19.01,7.42,x,y)).cut(cq.Solid.makeBox(4.4,4.4,1.8,cq.Vector(x-2.2,y-2.2,-14.2))).clean()
 if a.rigid_seat and not a.separate_seat:yoke=yoke.fuse(cylinder(a.seat_radius_mm,seat,-19-seat+.01,x,y)).cut(cylinder(1.15,seat-.01,-11.59-seat+.01,x,y)).clean()
 screw=cylinder(1,seat,8,x,y).fuse(cylinder(1.9,seat-1.3,1.3,x,y)).clean();nut=cq.Solid.makeBox(4,4,1.2,cq.Vector(x-2,y-2,-14.2)).cut(cylinder(1,-14.21,1.22,x,y));tool=cylinder(1.5,-35,seat-1.3+35-.01,x,y)
 objects={'sole':sole,'yoke':yoke,'screw':screw,'nut':nut};overlaps={}
 if a.separate_seat:
  assert a.rigid_seat
  objects['spacer']=cylinder(a.seat_radius_mm,seat,-19-seat,x,y).cut(cylinder(1.15,seat-.01,-19-seat+.02,x,y))
  for n in ['sole','yoke','screw']:overlaps['spacer_'+n]=objects['spacer'].intersect(objects[n]).Volume()
 for n,obj in objects.items():
  cq.exporters.export(obj,str(a.out/f'{side}_{n}.step'));overlaps[n+'_boot']=obj.intersect(parts['boot']).Volume()
 for n,m in [('sole','yoke'),('screw','sole'),('screw','yoke'),('screw','nut'),('nut','yoke')]:overlaps[n+'_'+m]=objects[n].intersect(objects[m]).Volume()
 overlaps['tool_sole']=tool.intersect(sole).Volume();overlaps['tool_yoke']=tool.intersect(yoke).Volume()
 valid=all(o.isValid() and len(o.Solids())==1 for o in objects.values());rows.append({'side':side,'source_sha256':{str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in paths.values()},'valid_single_solids':valid,'overlap_mm3':overlaps,'nominal_geometry_pass':valid and max(overlaps.values())<=.01,'head_recess_mm':seat-1.3+22,'nominal_thread_projection_mm':seat+8+13})
r={'rows':rows,'retention_strength_verified':False,'manufacturing_release':False};(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
