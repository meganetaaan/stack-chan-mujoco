"""Evaluate proposed dimensional envelopes, without claiming process capability."""
import argparse
import hashlib
import json
import math
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--spec', type=Path, default=Path('docs/prototype/mechanical/sole_spacer/specification.json'))
parser.add_argument('--out', type=Path, required=True)
a = parser.parse_args()
s = json.loads(a.spec.read_text())
m = s['mating_requirements_proposed']
for key in ['outer_diameter', 'inner_diameter', 'thickness']:
    v = s[key]
    if not 0 < v['min'] <= v['nominal'] <= v['max']:
        raise ValueError(f'Invalid dimensional interval: {key}')
radial = (m['sole_hole_diameter']['min'] - s['outer_diameter']['max']) / 2
bore_clearance = (s['inner_diameter']['min'] - m['screw_shank_diameter_max']) / 2
recess = m['sole_local_thickness']['min'] - s['thickness']['max'] - m['screw_head_height_max']
edge = s['edge_break_radial_max']
bearing_ro = s['outer_diameter']['min']/2 - edge
bearing_ri = s['inner_diameter']['max']/2 + edge
area = math.pi * (bearing_ro**2 - bearing_ri**2)
nominal_area = math.pi * (3**2 - 1.15**2)
r = {
    'scope': 'Worst dimensional bounds of proposed requirements; no strength or production qualification',
    'spec_sha256': hashlib.sha256(a.spec.read_bytes()).hexdigest(),
    'minimum_radial_sole_clearance_mm': radial,
    'minimum_radial_screw_clearance_mm': bore_clearance,
    'minimum_unloaded_head_recess_mm': recess,
    'remaining_budget_for_compression_wear_tilt_embedding_mm': recess-m['required_floor_recess'],
    'minimum_geometric_flat_bearing_annulus_mm2': area,
    'nominal_sharp_edge_bearing_annulus_mm2': nominal_area,
    'bearing_area_reduction_fraction': 1-area/nominal_area,
    'conditional_dimensional_gates': {
        'sole_radial_clearance': radial >= m['required_radial_assembly_clearance'],
        'screw_clearance': bore_clearance >= 0,
        'unloaded_floor_recess': recess >= m['required_floor_recess'],
    },
    'note': 'Annulus is geometric only; actual loaded contact area can be smaller. Prior nominal FE cannot establish tolerance-case stress.',
    'manufacturing_release': False,
    'unverified': s['unverified'],
}
a.out.mkdir(parents=True, exist_ok=False)
(a.out/'report.json').write_text(json.dumps(r, indent=2)+'\n')
print(json.dumps(r, indent=2))
