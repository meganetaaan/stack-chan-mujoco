"""Audit nominal clamp stack; CAD cylinders do not prove threaded engagement."""
import argparse, hashlib, json
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
root=Path('validation/yaw_integrated_candidate_v2');ip=root/'inventory.json';sp=root/'yaw_support_candidate.step'
items=json.loads(ip.read_text());items=items['parts'] if isinstance(items,dict) else items
solids=cq.importers.importStep(str(sp)).solids().vals();assert len(solids)==len(items)==52
parts={}
for item,solid in zip(items,solids):
 assert abs(solid.Volume()-item['volume_mm3'])<1e-5
 parts[item['name']]=solid
plan={'question':'What is the nominal clamp stack and screw protrusion at all eight plate joints?', 'source_sha256':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in [ip,sp]},'criterion':'Nominal bearing planes coincide and screw envelope extends through nut; no effective-thread or preload claim.', 'assumptions':['SLH-M2-10 underhead length 10 mm from existing inventory','Z-axis screws point upward','Nominal CAD only; no dimensional tolerances'], 'stop':'Eight existing joints, no strength calculation or geometry change.'}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');rows=[]
for side in ('left','right'):
 plate=parts[f'{side}_mount_plate'].BoundingBox()
 for i in range(4):
  key=f'{side}_plate_{i}';s=parts[key+'_screw'].BoundingBox();w=parts[key+'_washer'].BoundingBox();n=parts[key+'_nut'].BoundingBox()
  underhead=s.zmax-10
  row={'joint':key,'underhead_z_mm':underhead,'plate_bottom_z_mm':plate.zmin,'plate_top_z_mm':plate.zmax,'washer_bottom_z_mm':w.zmin,'washer_top_z_mm':w.zmax,'nut_bottom_z_mm':n.zmin,'nut_top_z_mm':n.zmax,'screw_tip_z_mm':s.zmax,'nominal_grip_mm':n.zmin-underhead,'nominal_nut_height_mm':n.zlen,'tip_protrusion_mm':s.zmax-n.zmax,'bearing_planes_match':abs(underhead-plate.zmin)<1e-6 and abs(w.zmax-n.zmin)<1e-6}
  rows.append(row)
result={'rows':rows,'nominal_stack_pass':all(r['bearing_planes_match'] and r['tip_protrusion_mm']>0 for r in rows),'effective_thread_engagement_verified':False,'preload_verified':False,'manufacturing_release':False}
(a.out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
