"""Propagate proposed rear-washer thickness into the existing bounded screw stack."""
import argparse, hashlib, json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--out',type=Path,required=True)
a=p.parse_args()
paths=[Path('validation/yaw_backing_stock_stack_v1/report.json'),Path('validation/rear_washer_clearance_v1/report.json')]
old,washer=[json.loads(x.read_text()) for x in paths]
for rel,sha in old['source_sha256'].items():
 assert hashlib.sha256(Path(rel).read_bytes()).hexdigest()==sha,rel
spec=washer['specification']['thickness_mm']
plan={'question':'Does the proposed washer thickness range prevent main bolts traversing the backing plate?',
 'acceptance':'Positive tip protrusion for all declared length/stock/washer endpoint combinations; no thread strength claim.',
 'stop':'Eight main bolts, eight endpoint combinations each; keepers not altered.',
 'datum':'Rear plate bearing surface and backing entry fixed; thicker washer moves bolt head and tip toward negative X.',
 'remaining_nominal':['rear plate thickness and placement','printed seat dimensions and compression','head actual seating','thread end forms']}
rows=[]
for row in old['rows']:
 if '_main_' not in row['name']:continue
 cases=[]
 for case in row['cases']:
  for t in [spec['min'],spec['max']]:
   shift=spec['nominal']-t
   tip=case['tip_x_mm']+shift
   protrusion=tip-case['exit_x_mm']
   # Independent underhead-length reconstruction: nominal seat + Ldelta - washer delta.
   independent=row['nominal_tip_x_mm']+case['length_delta_mm']-(t-spec['nominal'])
   assert abs(independent-tip)<1e-12
   cases.append({**case,'washer_thickness_mm':t,'tip_x_mm':tip,'protrusion_mm':protrusion,
                 'shaft_material_overlap_mm':min(case['stock_thickness_mm'],max(0,tip-row['entry_x_mm']))})
  assert cases[-1]['tip_x_mm'] < cases[-2]['tip_x_mm']
 rows.append({'name':row['name'],'cases':cases})
assert len(rows)==8 and all(len(r['cases'])==8 for r in rows)
cases=[c for r in rows for c in r['cases']]
report={'source_sha256':{str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in paths},'plan':plan,'rows':rows,
 'minimum_protrusion_mm':min(c['protrusion_mm'] for c in cases),
 'maximum_protrusion_mm':max(c['protrusion_mm'] for c in cases),
 'minimum_tip_x_mm':min(c['tip_x_mm'] for c in cases),'maximum_tip_x_mm':max(c['tip_x_mm'] for c in cases),
 'shaft_traverses_stock_for_declared_bounds':all(c['protrusion_mm']>0 for c in cases),
 'fully_formed_thread_engagement_min_mm':None,'neighbor_clearance_verified':False,
 'retention_strength_verified':False,'manufacturing_release':False}
a.out.mkdir(parents=True,exist_ok=False)
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ['source_sha256','plan','rows']}))
