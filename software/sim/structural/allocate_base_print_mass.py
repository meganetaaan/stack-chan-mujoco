"""Allocate printed base solids using the existing PETG comparison candidate."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--out', type=Path, required=True)
a = p.parse_args()
paths = [Path(x) for x in [
    'validation/yaw_inertial_ledger_v2/report.json',
    'validation/payload_inertial_replacement_v1/report.json',
    'board/mechanical/prototype/rc_battery_tray_revB/material_candidate.json']]
yaw, payload, material = [json.loads(x.read_text()) for x in paths]
# Reject stale upstream ledger; coefficients and fixed subtotal must share provenance.
assert payload['sources_sha256'][str(paths[0])] == hashlib.sha256(paths[0].read_bytes()).hexdigest()
names = ('body_shroud', 'left_yaw_fixed_support', 'right_yaw_fixed_support')
coefficients = yaw['homogeneous_density_coefficients_per_kg_m3']
rho = material['typical_density_g_cm3'] * 1000
allocated = {name: {k: (np.asarray(v) * rho).tolist() for k, v in coefficients[name].items()} for name in names}
subtotal = {k: (np.asarray(v) + sum(np.asarray(part[k]) for part in allocated.values())).tolist()
            for k, v in payload['updated_fixed_terms'].items()}
m = subtotal['mass_kg']
c = np.asarray(subtotal['first_moment_kg_m']) / m
inertia = np.asarray(subtotal['inertia_origin_kg_m2']) - m * (c @ c * np.eye(3) - np.outer(c, c))
principal = np.linalg.eigvalsh(inertia)
assert np.all(principal > 0) and principal[-1] <= sum(principal[:2])
remaining = {k: v for k, v in coefficients.items() if k not in names}
assert len(remaining) == 8 and all(k.endswith('rear_washer') for k in remaining)
report = {
    'sources_sha256': {str(x): hashlib.sha256(x.read_bytes()).hexdigest() for x in paths},
    'frame': yaw['frame'], 'candidate_density_kg_m3': rho,
    'assumption': 'Uniform solid PETG; typical density, not measured printed density or structural allowable.',
    'allocated_print_parts': allocated, 'subtotal_origin_terms': subtotal,
    'subtotal_com_m': c.tolist(), 'subtotal_inertia_com_kg_m2': inertia.tolist(),
    'remaining_density_coefficients_per_kg_m3': remaining,
    'remaining': [x for x in payload['remaining'] if not x.startswith('11 homogeneous')]
        + ['8 rear washers still need material/mass selection; do not confuse with the 8 already allocated mount washers.'],
    'whole_base_complete': False, 'model_updated': False, 'manufacturing_release': False}
a.out.mkdir(parents=True, exist_ok=False)
(a.out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'added_print_mass_kg': sum(x['mass_kg'] for x in allocated.values()), 'subtotal_kg': m}))
