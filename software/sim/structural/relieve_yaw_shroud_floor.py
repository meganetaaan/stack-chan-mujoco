"""Local shroud-floor relief for the inherited yaw support intersections."""
import argparse,hashlib,json
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
plan={'question':'Can local shroud-floor notches remove the inherited support intersection while retaining supports and rear corner seats?',
 'cutters':'X[-63.5,-52.2], Y=cy+/-19.3, Z[48.6,53.5], cy=+/-26 mm.',
 'basis':'Observed intersection X[-62.2,-53.5], Y=cy+/-18, Z[49.9,52.2], expanded 1.3 mm along all axes. Clearance must still be measured against entire support.',
 'criteria':{'single_valid_solid':True,'outer_bbox_delta_mm':1e-6,'support_overlap_max_mm3':.01,'support_gap_min_mm':1.3,'protected_seat_removed_mm3':1e-8},
 'protected':'Rear corner axes Y=+/-57, Z=8,120; radius 6 mm X[-70,-40] volumes.',
 'stop':'One pair of local notches, no geometry sweep or FE.',
 'limits':['Notches may reduce shroud stiffness and floor ligaments','Only nominal geometry; provisional 0.8 mm tolerance/deflection allocation','Assembly insertion path, fastener contact, full robot load path not verified','No manufacturing release']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
path=Path('validation/yaw_tool_access_v1/body_shroud.step');old=cq.importers.importStep(str(path)).val();new=old;hashes={str(path):hashlib.sha256(path.read_bytes()).hexdigest()}
for cy in [26,-26]:new=new.cut(cq.Solid.makeBox(11.3,38.6,4.9,cq.Vector(-63.5,cy-19.3,48.6)))
new=new.clean();removed=old.cut(new);b0=old.BoundingBox();b1=new.BoundingBox();bd=max(abs(getattr(b0,k)-getattr(b1,k)) for k in ['xmin','xmax','ymin','ymax','zmin','zmax'])
seats=[]
for y in [-57,57]:
 for z in [8,120]:
  probe=cq.Solid.makeCylinder(6,30,cq.Vector(-70,y,z),cq.Vector(1,0,0));seats.append({'yz_mm':[y,z],'removed_mm3':removed.intersect(probe).Volume()})
rows=[]
for side in ['left','right']:
 path=Path(f'validation/yaw_deep_side_ribs_v1/{side}_yaw_fixed_support.step');hashes[str(path)]=hashlib.sha256(path.read_bytes()).hexdigest();support=cq.importers.importStep(str(path)).val()
 before=old.intersect(support);gap=new.distance(support);overlap=new.intersect(support).Volume();cq.exporters.export(before,str(a.out/f'{side}_original_intersection.step'))
 rows.append({'side':side,'old_overlap_mm3':before.Volume(),'new_overlap_mm3':overlap,'gap_mm':gap,'residual_after_provisional_0_8_mm':gap-.8,'pass':overlap<=.01 and gap>=1.3-1e-6})
passed=new.isValid() and len(new.Solids())==1 and bd<=1e-6 and all(r['pass'] for r in rows) and all(s['removed_mm3']<=1e-8 for s in seats)
cq.exporters.export(new,str(a.out/'body_shroud.step'));cq.exporters.export(removed,str(a.out/'removed_floor_material.step'))
result={'source_sha256':hashes,'rows':rows,'protected_seats':seats,'valid_single_solid':new.isValid() and len(new.Solids())==1,'outer_bbox_delta_mm':bd,'removed_volume_mm3':removed.Volume(),'nominal_geometry_screen_pass':passed,'manufacturing_release':False,'strength_verified':False}
(a.out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
