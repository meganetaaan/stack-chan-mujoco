#!/usr/bin/env python3
"""Reconcile frozen r9 base inertial with its component provenance."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import numpy as np


def audit(root):
    source = root / 'validation/fast_turn_development_v1/packaging_cad_v5/report.json'
    target = root / 'software/sim/mujoco/assets/r9_fast_turn_v1/models/inertials.json'
    properties = json.loads(source.read_text())['properties']
    expected = json.loads(target.read_text())['base']
    records = {}
    for name, original in properties.items():
        if name.endswith('_yaw_coupler'):
            continue
        record = copy.deepcopy(original)
        if name.endswith('_screw_envelope'):
            scale = .00030 / record['mass_kg']
            record['mass_kg'] = .00030
            record['inertia_com_kg_m2'] = (np.array(record['inertia_com_kg_m2']) * scale).tolist()
            record['mass_basis'] = 'r9 generator explicit 0.30 g screw override'
        else:
            record['mass_basis'] = 'packaging report allocation'
        records[name] = record
    mass = sum(r['mass_kg'] for r in records.values())
    com = sum(r['mass_kg'] * np.array(r['com_base_m']) for r in records.values()) / mass
    inertia = np.zeros((3, 3))
    for r in records.values():
        d = np.array(r['com_base_m']) - com
        inertia += np.array(r['inertia_com_kg_m2']) + r['mass_kg'] * (d @ d * np.eye(3) - np.outer(d, d))
    errors = dict(mass_kg=abs(mass-expected['mass_kg']),
                  com_m=float(np.max(np.abs(com-expected['com_m']))),
                  inertia_kg_m2=float(np.max(np.abs(inertia-expected['inertia_kg_m2']))))
    printed = ['body_shroud', 'rear_cover', 'battery_tray', 'left_yaw_fixed_support', 'right_yaw_fixed_support']
    return dict(scope='Frozen r9 base provenance reconciliation only; no candidate dynamics validation',
                criteria={'absolute_error_each_quantity_max': 1e-12},
                passed=all(v <= 1e-12 for v in errors.values()), errors=errors,
                aggregate=dict(mass_kg=mass, com_m=com.tolist(), inertia_kg_m2=inertia.tolist()),
                inferred_printed_density_kg_m3={n: properties[n]['mass_kg']/properties[n]['volume_mm3']*1e9 for n in printed},
                components=records,
                unresolved=['25 g cables_and_fasteners reservation does not itemize hardware; new screws must not silently be added or subtracted from it.',
                            'Battery, converter and interface remain mass reservations, not selected production components.',
                            'Candidate PETG density 1270 differs from baseline 1240; geometry and material effects must be separated.',
                            'Candidate CAD, collision geometry and load exports are not updated by this audit.'],
                source_sha256={str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in (source,target,Path(__file__).resolve())})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    result = audit(root)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ('passed','errors','inferred_printed_density_kg_m3')}, indent=2))
    if not result['passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
