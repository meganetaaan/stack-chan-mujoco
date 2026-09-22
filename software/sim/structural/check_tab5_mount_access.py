"""Straight rear tool corridor at four verified Tab5 rear mounting coordinates."""
import hashlib,json
from pathlib import Path
import cadquery as cq
ROOT=Path(__file__).resolve().parents[3];out=ROOT/'validation/tab5_mount_access_v1';out.mkdir(exist_ok=True)
plan={'axis_x_range_mm':[-80,49],'axes_yz_mm':[[y,z] for y in [-60,60] for z in [52,124]],'corridor_radii_mm':[1.5,2.5],'basis':'Unselected straight tool corridors, not manufacturer tool geometry; end49 leaves3mm for future bracket/screw head behind Tab5 rear52','criteria':'No volume intersection >0.01mm3 with retained geometry','stop':'4 axes x2 radii; identify removable blockers, no shell modification or strength analysis'}
(out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
p=ROOT/'validation/torso_power_integration_v2';r=json.loads((p/'report.json').read_text());ss=cq.importers.importStep(str(p/'torso_candidate.step')).val().Solids();assert len(ss)==len(r['parts'])==100
parts=dict(zip([x['name'] for x in r['parts']],ss));files=[p/'report.json',p/'torso_candidate.step']
for n,f in {'tray':'validation/lb020_retention_v5/tray.step','battery':'validation/lb020_tray_v1/battery.step','strap_0':'validation/lb020_retention_v5/strap_0.step','strap_1':'validation/lb020_retention_v5/strap_1.step'}.items():
 path=ROOT/f;files.append(path);parts[n]=cq.importers.importStep(str(path)).val()
rows=[]
for y,z in plan['axes_yz_mm']:
 for radius in plan['corridor_radii_mm']:
  tool=cq.Solid.makeCylinder(radius,129,cq.Vector(-80,y,z),cq.Vector(1,0,0));hits=[]
  for n,s in parts.items():
   v=tool.intersect(s).Volume()
   if v>.01:hits.append({'part':n,'overlap_mm3':v})
  rows.append({'axis_yz_mm':[y,z],'radius_mm':radius,'blockers':hits})
result={'rows':rows,'source_sha256':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},'actual_tool_access_verified':False,'manufacturing_release':False}
(out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps([(x['axis_yz_mm'],x['radius_mm'],[h['part'] for h in x['blockers']]) for x in rows]))
