"""Resolve existing yaw fastener seating against the 2 mm structural plate.

Bounded nominal CAD check only: no material, preload or purchased tolerances.
"""
import argparse, csv, hashlib, json
from pathlib import Path
import cadquery as cq
ROOT=Path(__file__).resolve().parents[3]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--out',type=Path,required=True)
a=p.parse_args(); a.out.mkdir(parents=True,exist_ok=False)
plate_path=ROOT/'validation/rear_joint_assembly_development_v1/rear_joint_inset2_v1/rear_structural_plate.step'
fast_dir=ROOT/'validation/inset_yaw_assembly_development_v1/inset_fasteners_staged_v2'
support_dir=ROOT/'validation/inset_yaw_assembly_development_v1/yaw_inset_mount_v1'
plan={'question':'Can existing M3x16 envelopes seat against the 2 mm plate without changing support position?',
      'method':'Read STEP bounds, move only outer washer/bolt/key to plate rear face; check intersections and axial stack.',
      'stop':'One existing nominal assembly, eight fasteners; record any unresolved collision; no FE or dimension sweep.',
      'criteria':{'unintended_intersection_mm3':0.01,'minimum_nominal_thread_projection_mm':1.0},
      'criteria_origin':'Existing CAD screening assumptions; not manufacturer guarantees.',
      'limitations':['nominal dimensions','thread engagement and preload not verified','only plate/support/fastener subset','no tool motion or whole body clearance proof']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
source={}
def read(path):
 source[str(path.relative_to(ROOT))]=hashlib.sha256(path.read_bytes()).hexdigest()
 return cq.importers.importStep(str(path)).val()
plate=read(plate_path); assembly=cq.Assembly(name='yaw_plate_nominal')
assembly.add(plate,name='rear_structural_plate')
rows=[]; findings=[]
for side in ['left','right']:
 support=read(support_dir/f'{side}_yaw_fixed_support.step')
 assembly.add(support,name=f'{side}_support')
 for i in range(4):
  parts={k:read(fast_dir/f'{side}_{i}_{k}.step') for k in ['bolt','rear_washer','inner_washer','nut','rear_key','nut_driver']}
  old_overlap=parts['rear_washer'].intersect(plate).Volume()
  delta=plate.BoundingBox().xmin-parts['rear_washer'].BoundingBox().xmax
  for k in ['bolt','rear_washer','rear_key']:parts[k]=parts[k].translate((delta,0,0))
  seat=parts['rear_washer'].BoundingBox().xmin
  tip=parts['bolt'].BoundingBox().xmax
  nut_front=parts['nut'].BoundingBox().xmax
  row={'side':side,'index':i,'outer_parts_shift_x_mm':delta,'old_washer_plate_overlap_mm3':old_overlap,
       'bolt_seat_x_mm':seat,'nut_front_x_mm':nut_front,'stack_mm':nut_front-seat,
       'bolt_length_mm':tip-seat,'thread_projection_mm':tip-nut_front}
  rows.append(row)
  for k,s in parts.items():
   if k in ['rear_key','nut_driver']:continue
   assembly.add(s,name=f'{side}_{i}_{k}')
   for target,t in [('plate',plate),('support',support)]:
    overlap=s.intersect(t).Volume()
    findings.append({'side':side,'index':i,'part':k,'target':target,'overlap_mm3':overlap,'pass':overlap<=.01})
assembly.save(str(a.out/'yaw_plate_nominal.step'))
with (a.out/'fasteners.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
report={'rows':rows,'checks':findings,'subset_intersections_pass':all(x['pass'] for x in findings),
        'nominal_projection_pass':all(x['thread_projection_mm']>=1 for x in rows),
        'source_sha256':source,'manufacturing_release':False,'strength_verified':False,'limitations':plan['limitations']}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ['subset_intersections_pass','nominal_projection_pass','manufacturing_release']}))
