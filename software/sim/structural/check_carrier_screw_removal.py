"""Continuous axial removal of nominal screw envelopes in integrated torso."""
import hashlib,json,math
from pathlib import Path
import cadquery as cq
ROOT=Path(__file__).resolve().parents[3];out=ROOT/'validation/carrier_screw_removal_v1';out.mkdir(exist_ok=True)
plan={'travel_mm':12,'criterion':'No sweep volume overlap >0.01mm3 with every other assembly part','basis':'Union of translating coaxial shaft/head cylinders is exact for nominal cylindrical envelope; threads/socket unmodeled','stop':'Four outward screw paths and four inward nut escape paths after corresponding screw removal. No tool or hand acceptance.'}
(out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
p=ROOT/'validation/serviceable_torso_v1';r=json.loads((p/'report.json').read_text());ss=cq.importers.importStep(str(p/'assembly.step')).val().Solids();assert len(ss)==len(r['parts'])==111
parts=dict(zip([x['name'] for x in r['parts']],ss));rows=[]
for sign in [-1,1]:
 for z in [88,112]:
  name=f'new_{sign}_{z}_screw'
  def cyl(radius,length,y):return cq.Solid.makeCylinder(radius,length,cq.Vector(42,sign*y,z),cq.Vector(0,sign,0))
  initial=cyl(1.5,10,54).fuse(cyl(2.75,2,64));actual=parts[name]
  assert initial.cut(actual).Volume()<1e-6 and actual.cut(initial).Volume()<1e-6
  sweep=cyl(1.5,22,54).fuse(cyl(2.75,14,64));hits=[]
  for n,s in parts.items():
   if n==name:continue
   a,b=sweep.BoundingBox(),s.BoundingBox()
   if any(getattr(a,k+'max')<=getattr(b,k+'min') or getattr(b,k+'max')<=getattr(a,k+'min') for k in 'xyz'):continue
   v=sweep.intersect(s).Volume()
   if v>.01:hits.append({'part':n,'overlap_mm3':v})
  rows.append({'screw':name,'travel_mm':12,'end_tip_abs_y_mm':66,'end_head_outer_abs_y_mm':78,'blockers':hits})
nut_rows=[]
for sign in [-1,1]:
 for z in [88,112]:
  name=f'new_{sign}_{z}_nut';screw=f'new_{sign}_{z}_screw'
  plane=cq.Plane(origin=(42,sign*50,z),xDir=(1,0,0),normal=(0,sign,0))
  sweep=cq.Workplane(plane).polygon(6,5.5/math.cos(math.pi/6)).extrude(7.8).val()
  sweep=sweep.cut(cq.Solid.makeCylinder(1.5,7.8,cq.Vector(42,sign*50,z),cq.Vector(0,sign,0)))
  hits=[]
  for n,t in parts.items():
   if n in (name,screw):continue
   v=sweep.intersect(t).Volume()
   if v>.01:hits.append({'part':n,'overlap_mm3':v})
  nut_rows.append({'nut':name,'inward_translation_mm':5.4,'blockers':hits,'geometric_escape_route_exists':not hits})
result={'nut_escape_cases':nut_rows,'cases':rows,'source_sha256':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [p/'report.json',p/'assembly.step']},'nut_captive_verified':False,'tool_access_verified':False,'manufacturing_release':False}
(out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(rows))
