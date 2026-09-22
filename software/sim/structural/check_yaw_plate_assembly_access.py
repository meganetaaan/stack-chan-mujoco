"""Surrounding-part and tool-path screen of the v4 mounting plate fasteners."""
import argparse,hashlib,json,math
from pathlib import Path
import cadquery as cq
ROOT=Path(__file__).resolve().parents[3];p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
plan={'question':'Are plate fasteners and their two-sided tools accessible in the current upper body?', 'stop':'One neutral assembly; record stage dependencies, no geometry sweep.', 'criteria':{'clearance_mm':.9,'intersection_mm3':.01},'tools':{'lower_hex_key':'radius1.5, Z36.7..86.7','upper_nut_driver':'outer radius4, Z91.9..141.9, radius2.9 cavity first8 mm'},'limits':['Tool reservations, not selected purchased tools','No hand envelope or complete legs/harness','No torque/preload','Case TAP screw heads absent','Own plate/support seating verified separately; not a full self-interference audit']};(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');sources={}
def read(path):
 sources[str(path.relative_to(ROOT))]=hashlib.sha256(path.read_bytes()).hexdigest();return cq.importers.importStep(str(path)).val()
base=ROOT/'software/sim/mujoco/assets/r9_fast_turn_v1/cad'
targets={n:read(base/(n+'.step')) for n in ['Tab5','battery_tray','battery_2S_reservation','dedicated_5V_converter','TTL_interface','left_yaw_coupler','right_yaw_coupler']};targets['body_shroud']=read(ROOT/'validation/yaw_tool_access_v1/body_shroud.step')
rows=[]
for side,cy in [('left',26),('right',-26)]:
 for x in [-34,8.1]:
  for y in [cy-10,cy+10]:
   def cyl(r,h,z):return cq.Solid.makeCylinder(r,h,cq.Vector(x,y,z))
   shapes={'head':cyl(1.9,1.3,86.7),'shaft':cyl(1,10,88),'washer':cyl(3,.9,91).cut(cyl(1.15,.9,91)),'nut':cyl(2.829,1.2,91.9).cut(cyl(1,1.2,91.9)),'lower_key':cyl(1.5,50,36.7),'upper_driver':cyl(4,50,91.9).cut(cyl(2.9,8,91.9))}
   for name,s in shapes.items():
    sb=s.BoundingBox()
    for tn,t in targets.items():
     tb=t.BoundingBox();lower=math.sqrt(sum(max(0,getattr(sb,k+'min')-getattr(tb,k+'max'),getattr(tb,k+'min')-getattr(sb,k+'max'))**2 for k in 'xyz'))
     d=lower if lower>=.9 else float(s.distance(t));v=float(s.intersect(t).Volume()) if d<1e-6 else 0
     rows.append({'side':side,'x_mm':x,'y_mm':y,'part':name,'target':tn,'distance_mm':d,'distance_is_lower_bound':lower>=.9,'overlap_mm3':v,'pass':d>=.9 and v<=.01})
r={'rows':rows,'source_sha256':sources,'manufacturing_release':False,'limits':plan['limits']};(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'failures':[r for r in rows if not r['pass']]},indent=2))
