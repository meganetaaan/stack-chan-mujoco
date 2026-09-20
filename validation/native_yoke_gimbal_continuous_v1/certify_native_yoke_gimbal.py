"""Bound native yoke/gimbal clearance over a continuous ankle-roll interval."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import cadquery as cq

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--gimbal-dir',type=Path,required=True)
p.add_argument('--out',type=Path,required=True)
a=p.parse_args()
root=Path(__file__).resolve().parents[3]
if a.out.exists(): p.error('new output required')
a.out.mkdir(parents=True)
paths={s:{'gimbal':a.gimbal_dir/f'{s}_ankle_gimbal.step',
          'yoke':root/f'validation/native_horn_yoke_development_v1/v4/{s}_foot_yoke.step'} for s in ('left','right')}
plan={'range_rad':[-.34,.34],'required_nominal_clearance_mm':1.1,
      'allocation_mm':{'residual':.5,'surface_tolerances_total':.4,'relative_deflection_reservation':.2},
      'numerical_allowance_mm':1e-5,'minimum_interval_rad':1e-4,
      'bound':'distance(midpoint) - radius_bound * half_interval - numerical_allowance',
      'gimbal_pitch_to_roll_translation_mm':[26,0,10],
      'source_sha256':{str(f.resolve().relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for row in paths.values() for f in row.values()},
      'limitations':['Rigid CAD pair only; no boots, hardware, other leg, floor or harness.',
                     'Deflection and manufacturing tolerance are reserved, not verified.',
                     'Numerical allowance is assumed; CAD kernel is not interval arithmetic.']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
results=[]
for side,row in paths.items():
    moving=cq.importers.importStep(str(row['yoke'])).val()
    fixed=cq.importers.importStep(str(row['gimbal'])).val().translate((26,0,10))
    bb=moving.BoundingBox()
    radius=math.hypot(max(abs(bb.ymin),abs(bb.ymax)),max(abs(bb.zmin),abs(bb.zmax)))
    samples={};accepted=[];unresolved=[];witness=None;queue=[(-.34,.34)]
    def distance(angle):
        if angle not in samples:
            samples[angle]=moving.rotate((0,0,0),(1,0,0),math.degrees(angle)).distance(fixed)
        return samples[angle]
    while queue:
        lo,hi=queue.pop();mid=(lo+hi)/2
        for angle in (lo,mid,hi):
            if distance(angle)<1.10001:
                witness={'angle_rad':angle,'distance_mm':distance(angle)};break
        if witness:break
        lower=distance(mid)-radius*(hi-lo)/2-1e-5
        if lower>=1.1:accepted.append({'interval_rad':[lo,hi],'lower_bound_mm':lower})
        elif hi-lo<=1e-4:unresolved.append([lo,hi])
        else:queue.extend([(lo,mid),(mid,hi)])
    covered=sum(x['interval_rad'][1]-x['interval_rad'][0] for x in accepted)
    passed=not witness and not unresolved and math.isclose(covered,.68,abs_tol=1e-12)
    result={'side':side,'radius_bound_mm':radius,'continuous_pair_pass':passed,
            'covered_interval_rad':covered,'witness':witness,'unresolved_intervals':unresolved,
            'certified_intervals':accepted,'samples':[{'angle_rad':k,'distance_mm':v} for k,v in sorted(samples.items())]}
    results.append(result)
    print(json.dumps({'side':side,'continuous_pair_pass':passed,'samples':len(samples),'intervals':len(accepted),'minimum_bound_mm':min((x['lower_bound_mm'] for x in accepted),default=None)}),flush=True)
(a.out/'report.json').write_text(json.dumps({'results':results,'all_pairs_pass':all(x['continuous_pair_pass'] for x in results),'manufacturing_release':False},indent=2)+'\n')
