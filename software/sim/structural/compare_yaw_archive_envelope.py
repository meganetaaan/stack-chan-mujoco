"""Check six-response superposition against the prior direct comparison solve."""
import argparse
import json
from pathlib import Path
import numpy as np

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--envelope', type=Path, required=True)
p.add_argument('--comparison-plan', type=Path, required=True)
p.add_argument('--direct-report', type=Path, required=True)
a = p.parse_args()
report = json.loads((a.envelope / 'report.json').read_text())
witness = max(report['rows'], key=lambda r: r['selected_actual_displacement_mm'])
w = json.loads(a.comparison_plan.read_text())['source_case']['selected_wrench_N_Nmm']
u = np.array([np.load(a.envelope / f'unit_{i}.npz')['displacement_mm'] for i in range(6)])
actual = float(np.linalg.norm(np.tensordot(w, u, axes=(0, 0)), axis=1).max())
old = json.loads(a.direct_report.read_text())['rows'][0]['max_displacement_mm']
out = {'old_comparison_load_superposition_mm': actual, 'old_direct_solve_mm': old,
       'relative_difference': abs(actual / old - 1), 'worst_selected_case': witness,
       'witness_to_old_comparison_ratio': witness['selected_actual_displacement_mm'] / actual,
       'note': 'Worst of 38 selected samples, not proven maximum over 266000 samples. Same 3 mm linear FE mesh.'}
if out['relative_difference'] >= 1e-8:
    raise ValueError('Superposition does not reproduce the prior direct solve')
(a.envelope / 'comparison.json').write_text(json.dumps(out, indent=2) + '\n')
print(json.dumps(out, indent=2))
