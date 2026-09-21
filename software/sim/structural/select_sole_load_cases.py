"""Preserve simultaneous contact loads when selecting historical screening cases."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import numpy as np

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--source', type=Path, required=True)
p.add_argument('--out', type=Path, required=True)
a = p.parse_args()
a.out.mkdir(parents=True, exist_ok=False)
criteria = {
    'selection': 'min/max each signed wrench component and max force/moment norm, per foot',
    'purpose': 'Historical structural screening inputs, not a complete stress envelope',
    'wrench_match_atol': 1e-10,
    'latest_mass_required_for_release': True,
}
(a.out / 'plan.json').write_text(json.dumps(criteria, indent=2) + '\n')
npz = a.source / 'wrenches.npz'
contacts = a.source / 'contacts_local.jsonl.gz'
data = np.load(npz)
w = data['wrench_N_Nmm']
times = data['time_s']
assert w.shape == (len(times), 2, 6) and np.isfinite(w).all()
selected = {}
for side_id, side in enumerate(['left', 'right']):
    metrics = {name: w[:, side_id, i] for i, name in enumerate(['Fx', 'Fy', 'Fz', 'Mx', 'My', 'Mz'])}
    for name, v in metrics.items():
        for operation, index in [('min', int(np.argmin(v))), ('max', int(np.argmax(v)))]:
            selected.setdefault((index, side_id), []).append(f'{name}_{operation}')
    for name, indices in [('force_norm', slice(0, 3)), ('moment_norm', slice(3, 6))]:
        index = int(np.argmax(np.linalg.norm(w[:, side_id, indices], axis=1)))
        selected.setdefault((index, side_id), []).append(name + '_max')
rows = []
with gzip.open(contacts, 'rt') as f:
    count = 0
    for index, line in enumerate(f):
        sample = json.loads(line)
        count += 1
        assert abs(sample['time_s'] - times[index]) <= criteria['wrench_match_atol']
        for side_id, side in enumerate(['left', 'right']):
            if (index, side_id) not in selected:
                continue
            foot = next(x for x in sample['feet'] if x['side'] == side)
            assert np.allclose(foot['wrench_at_yoke_center_N_Nmm'], w[index, side_id], atol=criteria['wrench_match_atol'], rtol=0)
            rows.append({'sample_index': index, 'time_s': float(times[index]), 'selected_by': selected[index, side_id], **foot})
assert count == len(times)
report = {
    'source_sha256': {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in [npz, contacts]},
    'cases': rows, 'source_samples': count, 'selected_cases': len(rows),
    'manufacturing_release': False, 'latest_configuration_loads': False,
    'limitations': ['Recorded ground contacts only; attachment reactions and separate sole inertia require a free-body model.',
                   'Component extrema do not guarantee maximum stress, contact opening, or bolt load.',
                   'Do not mix components between cases or multiply by mass ratio to qualify changed gait.'],
}
(a.out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'selected_cases': len(rows), 'source_samples': count}))
