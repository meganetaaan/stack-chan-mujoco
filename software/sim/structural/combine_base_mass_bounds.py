"""Combine allocated base moments and catalog screw distribution bounds once."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--out', type=Path, required=True)
a = p.parse_args()
paths = [Path(x) for x in ['validation/rear_washer_clearance_v1/report.json',
 'validation/screw_mass_distribution_bounds_v1/report.json',
 'board/mechanical/prototype/yaw_support_candidate/current.json']]
washer, screws, pointer = [json.loads(x.read_text()) for x in paths]
inventory = Path(pointer['inventory'])
assert screws['source_sha256'][str(inventory)] == hashlib.sha256(inventory.read_bytes()).hexdigest()
for upstream, digest in washer['source_sha256'].items():
 assert hashlib.sha256(Path(upstream).read_bytes()).hexdigest() == digest, upstream
fixed = washer['subtotal_origin_terms']
aggregate = screws['aggregate']
names = [x['name'] for x in screws['parts']]
assert len(names) == len(set(names)) == 20
assert not set(names).intersection(washer['parts'])
assert np.isclose(sum(x['mass_kg'] for x in screws['parts']), aggregate['mass_kg'])
mass = fixed['mass_kg'] + aggregate['mass_kg']
first = {end: np.asarray(fixed['first_moment_kg_m']) + aggregate[f'first_moment_{end}_kg_m'] for end in ('min','max')}
origin = {end: np.asarray(fixed['inertia_origin_kg_m2']) + aggregate[f'inertia_origin_{end}_kg_m2'] for end in ('min','max')}
report = {
 'source_sha256': {str(x): hashlib.sha256(x.read_bytes()).hexdigest() for x in paths + [inventory]},
 'frame': 'base CAD origin; same frame as upstream ledgers',
 'allocated_fixed_mass_kg': fixed['mass_kg'], 'catalog_screws_mass_kg': aggregate['mass_kg'],
 'partial_base_mass_kg': mass,
 'partial_base_com_bounds_m': {k: (v/mass).tolist() for k,v in first.items()},
 'partial_base_first_moment_bounds_kg_m': {k: v.tolist() for k,v in first.items()},
 'partial_base_origin_inertia_element_bounds_kg_m2': {k:v.tolist() for k,v in origin.items()},
 'accounting': 'Washer report already contains fixed retained payload, replacement payload, metal, printed base and eight rear washers. Add only 20 screws; do not add base_print_mass separately.',
 'remaining': [x for x in washer['remaining'] if not x.startswith('20 screws')],
 'limitations': screws['limitations'] + [
  'Fixed subtotal retains density and uniform-payload comparison assumptions; it is not measured mass.',
  'These COM bounds apply only to the allocated subtotal, not the complete robot or base.',
  'Elementwise inertia endpoints need not be jointly realizable; do not write them as a MuJoCo inertia.',
  'Unallocated nuts, wiring and electronics are excluded, not assigned zero mass.'],
 'whole_base_complete': False, 'model_updated': False, 'manufacturing_release': False}
a.out.mkdir(parents=True,exist_ok=False)
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'partial_base_mass_kg':mass,'COM_bounds_m':report['partial_base_com_bounds_m']}))
