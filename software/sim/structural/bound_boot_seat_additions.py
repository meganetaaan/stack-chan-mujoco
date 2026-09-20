"""Bound added boot-seat clearance to servo CAD by rotation-invariant X separation."""
import argparse,hashlib,json
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[3]
if a.out.exists():p.error('new output required')
a.out.mkdir(parents=True)
step=root/'validation/x330_manufacturer_cad_v1/XL_XC_330.stp'
prior=root/'validation/boot_native_servo_bound_v1/report.json'
prior_plan=root/'validation/boot_native_servo_development_v1/plan.json'
old_plan=json.loads(prior_plan.read_text())
for name,digest in old_plan['source_sha256'].items():
 if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest:raise ValueError('changed prior input')
previous=json.loads(prior.read_text())
if not previous['all_pairs_pass']:raise ValueError('prior bound must pass')
paths=[step,prior,prior_plan]+[root/f'validation/{folder}/{side}_boot_shell.step' for side in ('left','right') for folder in ('boot_seats_development_v1','boot_rear_relief_development_v1/cad')]
plan={'criterion_mm':1.1,'numerical_allowance_mm':1e-5,'bound':'Both fixed and X-rotating servo parts retain their X coordinates. Separation of X bounding intervals is a lower bound on 3D clearance. New boot is contained in old boot union added solids.','source_sha256':{str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in paths},'limitations':['Inherits previous rigid motion and numerical assumptions.','No fastening hardware, deformation or manufacturing qualification.']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
servo=[s.rotate((0,0,0),(-1,1,-1),120).translate((-3.5,0,0)) for s in cq.importers.importStep(str(step)).val().Solids()]
rows=[]
for side in ('left','right'):
 old=cq.importers.importStep(str(root/f'validation/boot_rear_relief_development_v1/cad/{side}_boot_shell.step')).val()
 new=cq.importers.importStep(str(root/f'validation/boot_seats_development_v1/{side}_boot_shell.step')).val()
 added=new.cut(old);solids=added.Solids()
 if len(solids)!=4:raise ValueError('expected four additions')
 pairs=[]
 for j,s in enumerate(solids):
  b=s.BoundingBox()
  for i,part in enumerate(servo):
   c=part.BoundingBox();gap=max(b.xmin-c.xmax,c.xmin-b.xmax,0)-1e-5
   pairs.append({'addition_index':j,'servo_index':i,'x_separation_bound_mm':gap})
 lower=min(previous['minimum_bound_mm'],min(x['x_separation_bound_mm'] for x in pairs))
 rows.append({'side':side,'added_volume_mm3':added.Volume(),'minimum_added_bound_mm':min(x['x_separation_bound_mm'] for x in pairs),'combined_boot_bound_mm':lower,'passed':lower>=1.1,'pairs':pairs})
report={'rows':rows,'all_pairs_pass':all(x['passed'] for x in rows),'manufacturing_release':False}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps([{k:v for k,v in r.items() if k!='pairs'} for r in rows]))
