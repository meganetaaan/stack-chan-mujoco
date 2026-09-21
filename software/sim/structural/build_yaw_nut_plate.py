"""Machined threaded backing plate concept replacing four loose rear nuts per support."""
import argparse,json,hashlib
from pathlib import Path
import cadquery as cq
ROOT=Path(__file__).resolve().parents[3];p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
plan={'question':'Can a common metal threaded plate eliminate four internal nut-driver operations?', 'stop':'One 3x22x32 mm backing plate per support, nominal geometry and surrounding collision check.', 'design':{'plate_x_mm':[-53.5,-50.5],'thread':'four M3x0.5 through, 14x24 mm pattern','model_hole_diameter_mm':2.5,'retention':'central M2x0.4 through tapped hole reserved for separate keeper screw; keeper screw/length/approach not yet selected','material':'metal grade and thread stripping allowable TBD'},'criteria':{'nonmating_gap_mm':.9,'intersection_mm3':.01},'limits':['Pilot holes shown, actual threads not modeled','Nominal3 mm engagement not strength acceptance','Thread grade/manufacture/keeper not released','Contact at support face intentional','No tool approach or full assembly qualification']};(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');rows=[];sources={}
def read(path):sources[str(path.relative_to(ROOT))]=hashlib.sha256(path.read_bytes()).hexdigest();return cq.importers.importStep(str(path)).val()
base=ROOT/'software/sim/mujoco/assets/r9_fast_turn_v1/cad'
targets={n:read(base/(n+'.step')) for n in ['Tab5','battery_2S_reservation','battery_tray','dedicated_5V_converter','TTL_interface','left_yaw_coupler','right_yaw_coupler','left_yaw_motor_case','right_yaw_motor_case']}
for side,cy in [('left',26),('right',-26)]:
 bar=cq.Solid.makeBox(3,22,32,cq.Vector(-53.5,cy-11,54))
 for dy in [-7,7]:
  for z in [58,82]:bar=bar.cut(cq.Solid.makeCylinder(1.25,3,cq.Vector(-53.5,cy+dy,z),cq.Vector(1,0,0)))
 bar=bar.cut(cq.Solid.makeCylinder(.8,3,cq.Vector(-53.5,cy,70),cq.Vector(1,0,0))).clean();assert bar.isValid() and len(bar.Solids())==1
 cq.exporters.export(bar,str(a.out/f'{side}_threaded_backing_plate.step'))
 local={**targets,'support':read(ROOT/f'validation/yaw_metal_seat_v4/{side}_yaw_fixed_support.step'),'case_mount_plate':read(ROOT/f'validation/yaw_metal_seat_v4/{side}_mount_plate.step')}
 for n,t in local.items():
  d=float(bar.distance(t));v=float(bar.intersect(t).Volume()) if d<1e-6 else 0;rows.append({'side':side,'target':n,'distance_mm':d,'overlap_mm3':v,'pass':v<=.01 and (n=='support' or d>=.9)})
r={'rows':rows,'source_sha256':sources,'nominal_m3_engagement_mm':3,'nominal_m3_tip_projection_mm':1.8,'manufacturing_release':False,'strength_verified':False,'limits':plan['limits']};(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'failures':[r for r in rows if not r['pass']]},indent=2))
