"""Bound between-sample boot/servo clearance using endpoint rotation displacement."""
import argparse,hashlib,json,math
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[3]
source=root/'validation/boot_native_servo_development_v1'
if a.out.exists():p.error('new output required')
a.out.mkdir(parents=True)
plan=json.loads((source/'plan.json').read_text());data=json.loads((source/'report.json').read_text())
for name,digest in plan['source_sha256'].items():
 if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest:raise ValueError(f'changed input: {name}')
angles=plan['angles_rad'];rotating=set(plan['assumed_rotating_component_indices'])
criteria={'required_clearance_mm':1.1,'numerical_allowance_mm':1e-5,'range_rad':[-.34,.34],
          'bound':'min(endpoint distances) - R * interval_width / 2 - numerical allowance; nearest endpoint is at most half an interval away',
          'co_rotating_bound':'Rigid common rotation preserves pair distance; minimum sampled distance minus numerical allowance',
          'source_sha256':{str((source/n).relative_to(root)):hashlib.sha256((source/n).read_bytes()).hexdigest() for n in ['plan.json','report.json']},
          'limitations':['Conditional on previous motion group assignments and CAD distance numerical allowance.','No new hardware, harness, tolerances or measured deflection.']}
(a.out/'plan.json').write_text(json.dumps(criteria,indent=2)+'\n')
results=[]
for side in ('left','right'):
 shape=cq.importers.importStep(str(root/f'validation/boot_rear_relief_development_v1/cad/{side}_boot_shell.step')).val();bb=shape.BoundingBox()
 radius=math.hypot(max(abs(bb.ymin),abs(bb.ymax)),max(abs(bb.zmin),abs(bb.zmax)))
 for i in range(15):
  rows=sorted([r for r in data['rows'] if r['side']==side and r['component_index']==i],key=lambda r:r['angle_rad'])
  if [r['angle_rad'] for r in rows]!=angles:raise ValueError('incomplete or duplicate samples')
  intervals=[]
  for left,right in zip(rows,rows[1:]):
   width=right['angle_rad']-left['angle_rad']
   lower=min(left['distance_mm'],right['distance_mm'])-(0 if i in rotating else radius*width/2)-1e-5
   intervals.append({'range_rad':[left['angle_rad'],right['angle_rad']],'lower_bound_mm':lower})
  results.append({'side':side,'component_index':i,'product_name':rows[0]['product_name'],'radius_bound_mm':radius,'co_rotating':i in rotating,'minimum_bound_mm':min(x['lower_bound_mm'] for x in intervals),'intervals':intervals,'passed':all(x['lower_bound_mm']>=1.1 for x in intervals)})
report={'results':results,'minimum_bound_mm':min(x['minimum_bound_mm'] for x in results),'all_pairs_pass':all(x['passed'] for x in results),'manufacturing_release':False}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='results'}))
