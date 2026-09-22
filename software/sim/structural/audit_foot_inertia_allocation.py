#!/usr/bin/env python3
"""Reconstruct legacy ankle-roll inertia before replacing the foot assembly."""
import hashlib
import json
from pathlib import Path
import numpy as np
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]

def main():
    paths = [Path('validation/fast_turn_development_v1/feet_cad_v2/report.json'),
             Path('software/sim/mujoco/assets/r9_fast_turn_v1/models/inertials.json'),
             Path('validation/foot_body_ownership_v1/report.json')]
    parts, inertials, frozen = [json.loads((ROOT / p).read_text()) for p in paths]
    model_path = Path(frozen['model_path'])
    model_bytes = (ROOT/model_path).read_bytes()
    if hashlib.sha256(model_bytes).hexdigest() != frozen['model_sha256']:
        raise ValueError('Frozen model changed since ownership audit')
    model = ET.fromstring(model_bytes)
    paths.append(model_path)
    rows = []
    for side in ('left', 'right'):
        names = [side + '_' + s for s in ('foot_yoke', 'boot_shell', 'sole_TPU')]
        records = [parts['properties'][n] for n in names]
        mass = sum(r['mass_kg'] for r in records)
        com = sum(r['mass_kg'] * np.array(r['com_link_m']) for r in records) / mass
        inertia = np.zeros((3, 3))
        for r in records:
            d = np.array(r['com_link_m']) - com
            inertia += np.array(r['inertia_com_kg_m2']) + r['mass_kg'] * (d @ d * np.eye(3) - np.outer(d, d))
        expected = inertials[side + '_ankle_roll']
        old = model.find('.//body[@name="' + side + '_ankle_roll"]/inertial').attrib
        full = inertia[[0, 1, 2, 0, 0, 1], [0, 1, 2, 1, 2, 2]]
        # Absolute tolerances allow serialization rounding only, not design error.
        checks = {
            'r9_mass': abs(mass - expected['mass_kg']) < 1e-14,
            'r9_com': np.allclose(com, expected['com_m'], rtol=0, atol=1e-14),
            'r9_inertia': np.allclose(inertia, expected['inertia_kg_m2'], rtol=0, atol=1e-17),
            'frozen_mass': abs(mass - float(old['mass'])) < 1e-14,
            'frozen_com': np.allclose(com, np.fromstring(old['pos'], sep=' '), rtol=0, atol=1e-14),
            'frozen_inertia': np.allclose(full, np.fromstring(old['fullinertia'], sep=' '), rtol=0, atol=1e-17),
        }
        checks = {k: bool(v) for k, v in checks.items()}
        if not all(checks.values()):
            raise ValueError((side, checks))
        rows.append({'side': side, 'legacy_parts': dict(zip(names, [r['mass_kg'] for r in records])),
                     'mass_kg': mass, 'com_m': com.tolist(), 'inertia_kg_m2': inertia.tolist(), 'checks': checks})
    report = {'rows': rows, 'source_sha256': {str(p): hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths},
              'replacement_rule': 'Replace entire ankle_roll inertial with complete new foot assembly; do not add new rigid mass to legacy mass.',
              'legacy_foot_contains_motor_or_fasteners': False,
              'remaining': ['Select contact material and metal parts; complete new foot inertia.',
                            'Audit parent motor and horn allocations separately before modifying parent inertia.',
                            'Account for all assembly fasteners and harness omitted from legacy three-part foot.'],
              'model_updated': False, 'manufacturing_release': False}
    out = ROOT/'validation/foot_inertia_allocation_v1'
    out.mkdir(exist_ok=True)
    (out/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'all_checks_pass': True, 'mass_kg_per_foot': rows[0]['mass_kg']}))

if __name__ == '__main__':
    main()
