"""Check corrected yaw fasteners against existing upper-body assembly candidates."""
import argparse,hashlib,json
from pathlib import Path
import cadquery as cq
ROOT=Path(__file__).resolve().parents[3]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
base=ROOT/'software/sim/mujoco/assets/r9_fast_turn_v1/cad'
rear=ROOT/'validation/rear_joint_assembly_development_v1/rear_joint_inset2_v1'
fast=ROOT/'validation/inset_yaw_assembly_development_v1/inset_fasteners_staged_v2'
plan={'question':'Does the corrected outer seating create upper-body interference; can existing staged assembly still access fasteners?',
      'stop':'One nominal neutral assembly, complete hardware and two tool-installation stages; no geometry search.',
      'criteria':{'intersection_mm3':.01,'tool_nominal_clearance_mm':.9,'tool_residual_clearance_mm':.5,'two_surface_tolerance_budget_mm':.4},
      'criteria_source':'Existing Codex screening budgets, not measured manufacturing tolerances.',
      'limitations':['neutral upper body only','motor-case reservation CAD, not manufacturer internals','no cables or complete moving legs','simplified yaw nut-driver envelope','no strength or preload']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
sources={}
def read(path):
 sources[str(path.relative_to(ROOT))]=hashlib.sha256(path.read_bytes()).hexdigest();return cq.importers.importStep(str(path)).val()
parts={n:read(base/(n+'.step')) for n in ['Tab5','battery_2S_reservation','battery_tray','dedicated_5V_converter','TTL_interface','left_yaw_coupler','right_yaw_coupler','left_yaw_motor_case','right_yaw_motor_case']}
parts['body_shroud']=read(rear/'body_shroud.step')
# The plate/support mating checks are in yaw_plate_stack_integration_v1.
# Here include the body attachment hardware, which was absent from that subset.
for f in sorted(rear.glob('corner_*.step')):
 if not f.stem.endswith(('key','driver')):parts[f.stem]=read(f)
deferred={'dedicated_5V_converter','TTL_interface','left_yaw_coupler','right_yaw_coupler','left_yaw_motor_case','right_yaw_motor_case'}
checks=[]
for side in ['left','right']:
 for i in range(4):
  for kind in ['bolt','rear_washer','inner_washer','nut','rear_key','nut_driver']:
   shape=read(fast/f'{side}_{i}_{kind}.step')
   if kind in ['bolt','rear_washer','rear_key']:shape=shape.translate((-.2,0,0))
   tool=kind in ['rear_key','nut_driver']
   for name,part in parts.items():
    d=float(shape.distance(part));v=float(shape.intersect(part).Volume()) if d<1e-6 else 0.
    checks.append({'fastener':f'{side}_{i}_{kind}','part':name,'tool':tool,'distance_mm':d,'overlap_mm3':v,
                   'hardware_pass':None if tool else v<=.01,'tool_complete_pass':d>=.9 if tool else None,
                   'tool_staged_pass':(None if name in deferred else d>=.9) if tool else None})
report={'source_sha256':sources,'hardware_failures':[r for r in checks if r['hardware_pass'] is False],
        'tool_complete_failures':[r for r in checks if r['tool_complete_pass'] is False],
        'tool_staged_failures':[r for r in checks if r['tool_staged_pass'] is False],
        'checks':checks,'deferred_parts':sorted(deferred),'manufacturing_release':False,'limitations':plan['limitations']}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:len(report[k]) for k in ['hardware_failures','tool_complete_failures','tool_staged_failures']}))
