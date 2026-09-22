"""Two recessed keeper screws for preassembling a threaded backing plate."""
import argparse,json,hashlib
from pathlib import Path
import cadquery as cq
ROOT=Path(__file__).resolve().parents[3];p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--seat-shift-mm',type=float,default=0);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
shift=a.seat_shift_mm
plan={'question':'Can two M2x10 low-head keeper screws retain the backing plate before body attachment without rear plate overlap?', 'stop':'One keeper pattern, two supports; no load analysis.', 'candidate':'NBK SLH-M2-10, head diameter3.8 height1.3 nominal', 'geometry':{'keeper_z_mm':[64,76],'seat_x_mm':-60.9+shift,'tip_x_mm':-50.9+shift,'counterbore_diameter_mm':4.2,'clearance_hole_mm':2.3,'thread':'M2x0.4 through in backing plate; pilot only modeled'}, 'criteria':{'unintended_overlap_mm3':.01},'limits':['Keeper torque and stripping strength unknown','Threads/purchased tolerances not modeled','Two screws bound rotation only within hole clearance','Central unused hole from v1 retained as history','Main M3 fastening still required for service load']};(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');rows=[];sources={}
for side,cy in [('left',26),('right',-26)]:
 def read(rel):
  path=ROOT/rel;sources[rel]=hashlib.sha256(path.read_bytes()).hexdigest();return cq.importers.importStep(str(path)).val()
 support=read(f'validation/yaw_metal_seat_v4/{side}_yaw_fixed_support.step');bar=read(f'validation/yaw_threaded_backing_plate_v1/{side}_threaded_backing_plate.step');rear=read('validation/rear_joint_assembly_development_v1/rear_joint_inset2_v1/rear_structural_plate.step')
 for z in [64,76]:
  def cyl(r,L,x):return cq.Solid.makeCylinder(r,L,cq.Vector(x,cy,z),cq.Vector(1,0,0))
  support=support.cut(cyl(1.15,9,-62.3)).cut(cyl(2.1,1.4+shift,-62.3));bar=bar.cut(cyl(.8,3,-53.5))
  head=cyl(1.9,1.3,-62.2+shift);shaft=cyl(1,10,-60.9+shift);screw=head.fuse(shaft)
  rows.append({'side':side,'z_mm':z,'nominal_thread_entry_mm':2.6+shift,'nominal_tip_recess_mm':.4-shift,'head_rear_face_x_mm':-62.2+shift,'screw_rear_plate_overlap_mm3':screw.intersect(rear).Volume(),'screw_support_overlap_mm3':screw.intersect(support).Volume()})
  cq.exporters.export(screw,str(a.out/f'{side}_{z}_keeper_envelope.step'))
 support=support.clean();bar=bar.clean();assert all(s.isValid() and len(s.Solids())==1 for s in [support,bar])
 cq.exporters.export(support,str(a.out/f'{side}_yaw_fixed_support.step'));cq.exporters.export(bar,str(a.out/f'{side}_threaded_backing_plate.step'))
r={'rows':rows,'source_sha256':sources,'manufacturing_release':False,'strength_verified':False,'limits':plan['limits']};(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(rows,indent=2))
