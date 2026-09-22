"""Replace support/shroud volume overlap with a nominal unilateral rail seat."""
import argparse,hashlib,json
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
body_path=Path('validation/yaw_tool_access_v1/body_shroud.step');mom_path=Path('board/mechanical/prototype/yaw_support_candidate/revB/geometric_moments.json')
body=cq.importers.importStep(str(body_path)).val();mom=json.loads(mom_path.read_text())['parts']
plan={'question':'Can support lower ends meet the retained shroud rail at Z52.2 without overlap or loss of the rear bolt-seat core?',
 'operation':'Remove support material below Z52.2; leave body unchanged. This is an intended contacting interface, not a free-clearance pair.',
 'criteria':{'max_overlap_mm3':.01,'minimum_contact_area_mm2':0,'protected_rear_radius_mm':3.5,'max_protected_removed_mm3':1e-8,'one_valid_solid':True,'no_external_expansion':True},
 'contact_area_method':'Intersect body slab Z52.19..52.2 with support slab Z52.2..52.21 shifted down 0.01; volume/0.01 is nominal common footprint.',
 'stop':'One seating plane, both sides; no mesh or size sweep.',
 'limits':['Zero nominal gap is not a manufacturing tolerance strategy','Rear land outer rim below seat may be reduced; protected radius is only geometry, not bearing allowable','Unilateral rail contact may lift off; do not bond in FE or assign tensile/friction capacity','Load sharing, insertion, preload, printed flatness and creep unresolved','No manufacturing release']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [body_path,mom_path]};rows=[]
for side in ['left','right']:
 path=Path(f'validation/yaw_deep_side_ribs_v1/{side}_yaw_fixed_support.step');hashes[str(path)]=hashlib.sha256(path.read_bytes()).hexdigest();old=cq.importers.importStep(str(path)).val()
 new=old.cut(cq.Solid.makeBox(200,200,152.2,cq.Vector(-100,-100,-100))).clean();removed=old.cut(new)
 b0,b1=old.BoundingBox(),new.BoundingBox();expansion=max([getattr(b0,k+'min')-getattr(b1,k+'min') for k in 'xyz']+[getattr(b1,k+'max')-getattr(b0,k+'max') for k in 'xyz'])
 protected=[]
 for item in mom:
  if item['name'].startswith(side+'_rear_') and item['name'].endswith('_bolt'):
   x,y,z=[v*1000 for v in item['com_assembly_m']];core=cq.Solid.makeCylinder(3.5,8.7,cq.Vector(-62.2,y,z),cq.Vector(1,0,0))
   protected.append({'bolt':item['name'],'axis_yz_mm':[y,z],'removed_mm3':removed.intersect(core).Volume()})
 upper=new.intersect(cq.Solid.makeBox(200,200,.01,cq.Vector(-100,-100,52.2))).translate((0,0,-.01))
 lower=body.intersect(cq.Solid.makeBox(200,200,.01,cq.Vector(-100,-100,52.19)))
 area=upper.intersect(lower).Volume()/.01;overlap=new.intersect(body).Volume()
 passed=new.isValid() and len(new.Solids())==1 and expansion<1e-6 and overlap<=.01 and area>0 and len(protected)==4 and all(v['removed_mm3']<1e-8 for v in protected)
 cq.exporters.export(new,str(a.out/f'{side}_yaw_fixed_support.step'));cq.exporters.export(removed,str(a.out/f'{side}_removed_lower_support.step'))
 rows.append({'side':side,'single_valid_solid':new.isValid() and len(new.Solids())==1,'external_expansion_mm':expansion,'removed_volume_mm3':removed.Volume(),'old_body_overlap_mm3':old.intersect(body).Volume(),'new_body_overlap_mm3':overlap,'nominal_body_distance_mm':new.distance(body),'nominal_common_contact_area_mm2':area,'protected_rear_seats':protected,'geometry_screen_pass':passed})
(a.out/'report.json').write_text(json.dumps({'source_sha256':hashes,'rows':rows,'body_modified':False,'manufacturing_release':False,'strength_verified':False},indent=2)+'\n');print(json.dumps(rows,indent=2))
