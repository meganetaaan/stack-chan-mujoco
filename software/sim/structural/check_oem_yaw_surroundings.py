"""Screen surrounding parts before designing a new OEM-frame support."""
import argparse,hashlib,json
from pathlib import Path
import cadquery as cq
ROOT=Path(__file__).resolve().parents[3];p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
plan={'question':'Are there non-shelf collisions that would prevent OEM side-frame adoption?', 'stop':'One neutral configuration of all four frames; no motion or pose sweep.', 'criteria':{'intersection_mm3':.01,'nonmating_nominal_clearance_mm':.9}, 'criteria_origin':'Inherited 0.4 mm tolerance plus 0.5 mm residual screening budget, not measured capability', 'limitations':['Neutral pose only','No complete legs or harness','No screw/tool envelopes','Frame-to-support fastening not designed']};(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');sources={}
def read(p):
 sources[str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest();return cq.importers.importStep(str(p)).val()
base=ROOT/'software/sim/mujoco/assets/r9_fast_turn_v1/cad'
targets={n:read(base/(n+'.step')) for n in ['Tab5','battery_tray','battery_2S_reservation','dedicated_5V_converter','TTL_interface','left_yaw_coupler','right_yaw_coupler']}
targets['body_shroud']=read(ROOT/'validation/yaw_tool_access_v1/body_shroud.step');targets['rear_plate']=read(ROOT/'validation/rear_joint_assembly_development_v1/rear_joint_inset2_v1/rear_structural_plate.step')
frames={p.stem:read(p) for p in sorted((ROOT/'validation/yaw_oem_side_frame_fit_v1').glob('*_frame.step'))};rows=[]
for n,f in frames.items():
 for tn,t in {**targets,**{k:v for k,v in frames.items() if k!=n}}.items():
  d=float(f.distance(t));v=float(f.intersect(t).Volume()) if d<1e-6 else 0
  rows.append({'frame':n,'target':tn,'distance_mm':d,'overlap_mm3':v,'intersection_pass':v<=.01,'clearance_pass':d>=.9})
r={'rows':rows,'source_sha256':sources,'manufacturing_release':False,'limitations':plan['limitations']};(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'failures':[r for r in rows if not r['intersection_pass'] or not r['clearance_pass']]},indent=2))
