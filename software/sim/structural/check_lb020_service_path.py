"""Continuous swept-box screen for LB-020 service; no sampled-frame clearance claim."""
import hashlib,json
from pathlib import Path
import cadquery as cq
ROOT=Path(__file__).resolve().parents[3];out=ROOT/'validation/lb020_service_path_v1';out.mkdir(exist_ok=True)
plan={'battery_xyz_mm':[24,70,36],'center_mm':[29,0,80],'lift_mm':9,'front_endpoint_center_x_mm':81,'criteria':'No swept volume overlap above0.01mm3 with retained parts','stop':'Six straight routes and one lift-then-forward route, with/without Tab5. No free path optimization.','assumptions':['Straps completely removed','Battery electrically disconnected','No cable/connector/hand envelope'],'lift_basis':'Battery bottom62+9=71 exceeds tray wall top70 by1mm nominal; not tolerance qualification'}
(out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
p=ROOT/'validation/torso_power_integration_v2';r=json.loads((p/'report.json').read_text());ss=cq.importers.importStep(str(p/'torso_candidate.step')).val().Solids();assert len(ss)==len(r['parts'])==100
parts={x['name']:s for x,s in zip(r['parts'],ss) if x['name'] not in ('battery','tray')}
tray=ROOT/'validation/lb020_retention_v5/tray.step';parts['tray']=cq.importers.importStep(str(tray)).val()
def sweep(start,end):
 d=[24+abs(end[0]-start[0]),70+abs(end[1]-start[1]),36+abs(end[2]-start[2])];c=[(a+b)/2 for a,b in zip(start,end)]
 assert sum(a!=b for a,b in zip(start,end))==1
 return cq.Workplane('XY').box(*d).translate(tuple(c)).val()
def inspect(label,start,end,removed=()):
 shape=sweep(start,end);hits=[]
 for n,s in parts.items():
  if n in removed:continue
  v=shape.intersect(s).Volume()
  if v>.01:hits.append({'part':n,'overlap_mm3':v})
 return {'segment':label,'start_mm':start,'end_mm':end,'removed_parts':list(removed),'blocking_parts':hits,'nominal_path_clear':not hits}
rows=[]
for axis,(lo,hi,half) in enumerate([(-67.7,64,12),(-64,64,35),(0,128,18)]):
 for sign,bound in [(-1,lo),(1,hi)]:
  end=[29,0,80];end[axis]=bound+sign*(half+5)
  rows.append(inspect('XYZ'[axis]+('+' if sign>0 else '-'),[29,0,80],end))
service=[]
for removed in [(),('Tab5',)]:
 service.append({'removed_parts':list(removed),'segments':[inspect('lift',[29,0,80],[29,0,89],removed),inspect('forward',[29,0,89],[81,0,89],removed)]})
result={'method':'Exact swept rectangular prism for fixed-orientation axis translation','straight_routes':rows,'lift_forward_routes':service,'source_sha256':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [p/'report.json',p/'torso_candidate.step',tray]},'service_qualified':False,'manufacturing_release':False}
(out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'straight':[(x['segment'],[h['part'] for h in x['blocking_parts']]) for x in rows],'lift_forward':[(x['removed_parts'],[(s['segment'],[h['part'] for h in s['blocking_parts']]) for s in x['segments']]) for x in service]}))
