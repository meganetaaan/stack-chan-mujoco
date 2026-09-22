"""Slide-in nut covers retained by rails; closure at Tab5 requires separate verification."""
import hashlib,json
from pathlib import Path
import cadquery as cq
ROOT=Path(__file__).resolve().parents[3];out=ROOT/'validation/carrier_nut_covers_v2';out.mkdir(exist_ok=True)
plan={'cap_bounds_x_mm':[38.4,51.8],'cap_abs_y_mm':[54.1,54.9],'cap_height_mm':6.0,'rail_inner_lip_abs_y_mm':[53,54],'rail_slot_half_height_mm':3.2,'basis':'Print geometry assumptions; no friction/elastic interference relied upon','criteria':['Connected carrier','Covers do not overlap assembled parts','Inward nut escape intersects covers'],'stop':'One cover geometry and nominal interference/escape screen; insertion and capture in all directions separate'}
(out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
p=ROOT/'validation/serviceable_torso_v1';r=json.loads((p/'report.json').read_text());ss=cq.importers.importStep(str(p/'assembly.step')).val().Solids();assert len(ss)==len(r['parts'])==111
parts=dict(zip([x['name'] for x in r['parts']],ss));carrier=parts.pop('new_carrier');covers={}
def box(d,c):return cq.Workplane('XY').box(*d).translate(tuple(c)).val()
for sign in [-1,1]:
 for z in [88,112]:
  for dz in [-1,1]:
   carrier=carrier.fuse(box([13.8,2,1],[44.9,sign*54,z+dz*3.7]))
   carrier=carrier.fuse(box([13.8,1,1.4],[44.9,sign*53.5,z+dz*2.9]))
  carrier=carrier.fuse(box([1,2,8],[37.7,sign*54,z]))
  cap=box([13.4,.8,6],[45.1,sign*54.5,z])
  cap=cap.cut(cq.Solid.makeCylinder(1.7,2,cq.Vector(42,sign*53.5,z),cq.Vector(0,sign,0)))
  covers[f'cover_{sign}_{z}']=cap
carrier=carrier.clean();hits=[]
for n,s in {'carrier':carrier,**covers}.items():
 for m,t in parts.items():
  v=s.intersect(t).Volume()
  if v>.01:hits.append({'parts':[n,m],'overlap_mm3':v})
internal=[{'cover':n,'overlap_mm3':s.intersect(carrier).Volume()} for n,s in covers.items()]
escape=[]
for sign in [-1,1]:
 for z in [88,112]:
  nut=parts[f'new_{sign}_{z}_nut'];moved=nut.translate((0,-sign*1,0));cap=covers[f'cover_{sign}_{z}']
  escape.append({'nut':f'new_{sign}_{z}_nut','inward_move_mm':1,'intersection_with_cover_mm3':moved.intersect(cap).Volume()})
insertion=[]
for n,s in covers.items():
 b=s.BoundingBox();travel=20
 sweep=box([b.xlen+travel,b.ylen,b.zlen],[(b.xmin+b.xmax+travel)/2,(b.ymin+b.ymax)/2,(b.zmin+b.zmax)/2])
 blockers=[]
 for m,t in {'carrier':carrier,**parts}.items():
  if m=='Tab5' or (m.startswith('new_') and m.endswith('_screw')):continue
  v=sweep.intersect(t).Volume()
  if v>.01:blockers.append({'part':m,'overlap_mm3':v})
 insertion.append({'cover':n,'forward_travel_mm':travel,'blockers':blockers})
result={'cover_insertion_checks':insertion,'carrier_valid':carrier.isValid(),'carrier_solids':len(carrier.Solids()),'external_overlaps':hits,'cover_carrier_overlaps':internal,'nut_escape_checks':escape,'source_sha256':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [p/'report.json',p/'assembly.step']},'manufacturing_release':False,'limits':['Nominal gaps .1mm through thickness and .2mm transverse are unqualified print allowances','Insertion assumes Tab5 and side screws absent; hand access and all-direction capture unproven','Rails and cover strength unqualified']}
for n,s in {'carrier':carrier,**covers}.items():cq.exporters.export(s,str(out/(n+'.step')))
(out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
