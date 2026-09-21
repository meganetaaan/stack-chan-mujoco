"""Conditional nut mass ceiling using square stock, not collision-cylinder volume."""
import argparse, hashlib, json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--out',type=Path,required=True)
p.add_argument('--density-ceiling-kg-m3',type=float,required=True)
a=p.parse_args()
if not 0<a.density_ceiling_kg_m3<1e5: p.error('Expected positive finite engineering density ceiling')
paths=[Path(x) for x in ['docs/prototype/mechanical/sole_spacer/nut_candidate.json',
 'board/mechanical/prototype/yaw_support_candidate/revB/inventory.json',
 'validation/base_mass_bounds_v1/report.json']]
spec,inv,base=[json.loads(x.read_text()) for x in paths]
nuts=[x for x in inv['parts'] if x['name'].endswith('_nut')]
assert len(nuts)==8 and len(set(x['name'] for x in nuts))==8
assert all('PTS A56202' in x['note'] for x in nuts)
assert base['source_sha256'][str(paths[1])]==hashlib.sha256(paths[1].read_bytes()).hexdigest()
v=spec['across_flats_mm'][1]**2*spec['thickness_mm'][1]
m=v*1e-9*a.density_ceiling_kg_m3
report={'source_sha256':{str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in paths},
 'part':spec['part_number'],'quantity_yaw_assembly':8,
 'bounding_stock_volume_per_nut_mm3':v,'density_ceiling_assumption_kg_m3':a.density_ceiling_kg_m3,
 'density_ceiling_source':'Explicit engineering assumption, not an A2 supplier guarantee',
 'mass_ceiling_per_nut_kg':m,'total_nut_mass_ceiling_kg':8*m,
 'partial_base_mass_plus_nuts_ceiling_kg':base['partial_base_mass_kg']+8*m,
 'nominal_nut_mass_kg':None,
 'excluded':['Nut hole and chamfer removal are not credited to the ceiling.','Other unallocated base components remain excluded.'],
 'limitations':['Requires actual part inside the specified square stock and actual density below the assumed ceiling.',
 'The inventory cylinders are collision envelopes, not physical material volumes.',
 'This is a conditional mass ceiling only; no nut COM or inertia is assigned.',
 'Underlying partial base mass is a comparison, so the sum is not a guaranteed manufactured base upper bound.'],
 'physical_mass_bound_qualified':False,'whole_base_complete':False,'model_updated':False}
a.out.mkdir(parents=True,exist_ok=False)
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'nut_mass_ceiling_g':8*m*1000,'partial_sum_g':report['partial_base_mass_plus_nuts_ceiling_kg']*1000}))
