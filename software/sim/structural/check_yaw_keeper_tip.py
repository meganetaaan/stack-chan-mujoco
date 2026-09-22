"""Neighbor clearance for protruding v2 keeper screws; no thread strength proof."""
import argparse,json,hashlib
from pathlib import Path
import cadquery as cq
ROOT=Path(__file__).resolve().parents[3];p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
plan={'question':'Does 0.6 mm nominal keeper tip protrusion cause a nonmating clearance failure?', 'stop':'Four complete keeper envelopes against fixed reservations and mounting plates, one pose.', 'criteria':{'gap_mm':.9,'overlap_mm3':.01},'limits':['Nominal head/length','Thread contact excluded','No wiring or complete robot','Does not qualify keeper load']};(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');sources={}
def read(p):sources[str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest();return cq.importers.importStep(str(p)).val()
base=ROOT/'software/sim/mujoco/assets/r9_fast_turn_v1/cad';targets={n:read(base/(n+'.step')) for n in ['Tab5','battery_tray','battery_2S_reservation','dedicated_5V_converter','TTL_interface','left_yaw_motor_case','right_yaw_motor_case','left_yaw_coupler','right_yaw_coupler']}
for side in ['left','right']:targets[side+'_mount_plate']=read(ROOT/f'validation/yaw_metal_seat_v4/{side}_mount_plate.step')
rows=[]
for side in ['left','right']:
 for z in [64,76]:
  s=read(ROOT/f'validation/yaw_backing_keeper_v2/{side}_{z}_keeper_envelope.step')
  for n,t in targets.items():
   d=float(s.distance(t));v=float(s.intersect(t).Volume()) if d<1e-6 else 0;rows.append({'side':side,'z_mm':z,'target':n,'gap_mm':d,'overlap_mm3':v,'pass':d>=.9 and v<=.01})
r={'rows':rows,'source_sha256':sources,'nominal_head_recess_mm':1,'head_recess_budget':{'two_boundary_errors_mm':.4,'head_height_extra_mm':.1,'remaining_mm':.5,'status':'Codex provisional assumptions, not confirmed manufacturer tolerances'},'axial_screw_length_inside_plate_max_mm':3,'manufacturing_release':False};(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'failures':[r for r in rows if not r['pass']],'minimum_gap_mm':min(r['gap_mm'] for r in rows)}))
