"""Check that installed metal plates do not obstruct later support-to-body tools."""
import argparse,json,hashlib,math
from pathlib import Path
import cadquery as cq
ROOT=Path(__file__).resolve().parents[3];p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--wera',action='store_true');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
plan={'question':'Can the existing rear support tools operate after plate fasteners are installed?', 'stop':'16 rear tools against added plates and hardware only; no sweep or pose optimization.', 'criteria':{'clearance_mm':.9,'intersection_mm3':.01},'limits':['Inherited simplified rear tool envelopes','Existing body/stage evidence remains separate','No actual torque or driver-head fit','No case TAP hardware or wires']};plan.update({'tool_model':'Wera 05118126001; blade OD7.8 x60; handle OD13 x97; cavity ID6.4 x8 assumed; tool starts X=-53' if a.wera else 'inherited', 'extra_targets':['Tab5','battery_tray','battery_2S_reservation','body_shroud'] if a.wera else []});(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');sources={}
def read(path):
 sources[str(path.relative_to(ROOT))]=hashlib.sha256(path.read_bytes()).hexdigest();return cq.importers.importStep(str(path)).val()
targets={}
for side,cy in [('left',26),('right',-26)]:
 targets[side+'_plate']=read(ROOT/f'validation/yaw_metal_seat_v4/{side}_mount_plate.step')
 for i,(x,y) in enumerate(( (x,y) for x in [-34,8.1] for y in [cy-10,cy+10])):
  def cyl(r,h,z):return cq.Solid.makeCylinder(r,h,cq.Vector(x,y,z))
  for n,s in {'head':cyl(1.9,1.3,86.7),'shaft':cyl(1,10,88),'washer':cyl(3,.9,91).cut(cyl(1.15,.9,91)),'nut':cyl(2.829,1.2,91.9).cut(cyl(1,1.2,91.9))}.items():targets[f'{side}_{i}_{n}']=s
if a.wera:
 for n in ['Tab5','battery_tray','battery_2S_reservation']:
  targets[n]=read(ROOT/f'software/sim/mujoco/assets/r9_fast_turn_v1/cad/{n}.step')
 targets['body_shroud']=read(ROOT/'validation/yaw_tool_access_v1/body_shroud.step')
rows=[]
for side in ['left','right']:
 for i in range(4):
  for kind in ['rear_key','nut_driver']:
   path=ROOT/f'validation/inset_yaw_assembly_development_v1/inset_fasteners_staged_v2/{side}_{i}_{kind}.step';s=read(path)
   if kind=='rear_key':s=s.translate((-.2,0,0))
   if a.wera and kind=='nut_driver':
    b=s.BoundingBox();y=(b.ymin+b.ymax)/2;z=(b.zmin+b.zmax)/2
    def cyl(r,length,x):return cq.Solid.makeCylinder(r,length,cq.Vector(x,y,z),cq.Vector(1,0,0))
    s=cyl(3.9,60,-53).fuse(cyl(6.5,97,7)).cut(cyl(3.2,8,-53))
   sb=s.BoundingBox()
   for tn,t in targets.items():
    tb=t.BoundingBox();lower=math.sqrt(sum(max(0,getattr(sb,k+'min')-getattr(tb,k+'max'),getattr(tb,k+'min')-getattr(sb,k+'max'))**2 for k in 'xyz'));d=lower if lower>=.9 else float(s.distance(t));v=float(s.intersect(t).Volume()) if d<1e-6 else 0
    rows.append({'tool':f'{side}_{i}_{kind}','target':tn,'distance_mm':d,'distance_is_lower_bound':lower>=.9,'overlap_mm3':v,'pass':d>=.9 and v<=.01})
r={'tool_model':'Wera 05118126001 nominal; cavity ID6.4 x8 assumed' if a.wera else 'inherited', 'rows':rows,'source_sha256':sources,'stage_increment_pass':all(r['pass'] for r in rows),'manufacturing_release':False,'limits':plan['limits']};(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'failures':[r for r in rows if not r['pass']]},indent=2))
