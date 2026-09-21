"""One flange-edge relief comparison, preserving the failed unmodified design."""
import argparse,json,hashlib
from pathlib import Path
import cadquery as cq
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
ROOT=Path(__file__).resolve().parents[3];p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
plan={'question':'Can a 0.6 mm outer flange edge chamfer meet neutral clearance, and what hole ligament does it consume?', 'stop':'One candidate; report ligament and clearance together; no strength qualification or further sweep.', 'chamfer_mm':.6,'flange_radius_mm':8,'hole_pitch_radius_mm':6,'hole_radius_mm':1.1,'nominal_clearance_criterion_mm':.9,'criterion_origin':'Existing 0.4 tolerance + 0.5 residual budget','limitations':['Neutral pose only','Thin ligament not strength-qualified','Flange mating area changes','No actual fastener seating or clamping proof']};(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');rows=[];sources={}
for side,cy in [('left',26),('right',-26)]:
 path=ROOT/f'software/sim/mujoco/assets/r9_fast_turn_v1/cad/{side}_yaw_coupler.step';sources[str(path.relative_to(ROOT))]=hashlib.sha256(path.read_bytes()).hexdigest();original=cq.importers.importStep(str(path)).val()
 outer=cq.Solid.makeCylinder(8,.6,cq.Vector(-5,cy,61.4));inner=cq.Solid.makeCone(8,7.4,.6,cq.Vector(-5,cy,61.4));candidate=original.cut(outer.cut(inner)).clean();assert candidate.isValid() and len(candidate.Solids())==1
 cq.exporters.export(candidate,str(a.out/f'{side}_yaw_coupler.step'))
 for sign in [-1,1]:
  fp=ROOT/f'validation/yaw_oem_side_frame_fit_v1/{side}_{sign}_frame.step';sources[str(fp.relative_to(ROOT))]=hashlib.sha256(fp.read_bytes()).hexdigest();f=cq.importers.importStep(str(fp)).val();d=BRepExtrema_DistShapeShape(f.wrapped,original.wrapped);d.Perform();q=d.PointOnShape2(1);v=float(candidate.distance(f))
  rows.append({'side':side,'frame_sign':sign,'original_distance_mm':d.Value(),'original_closest_coupler_point':[q.X(),q.Y(),q.Z()],'candidate_distance_mm':v,'clearance_pass':v>=.9,'removed_volume_mm3':original.Volume()-candidate.Volume()})
r={'rows':rows,'original_top_hole_ligament_mm':8-6-1.1,'candidate_top_hole_ligament_mm':7.4-6-1.1,'source_sha256':sources,'manufacturing_release':False,'strength_verified':False,'limitations':plan['limitations']};(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
