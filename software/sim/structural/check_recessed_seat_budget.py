"""Dimensional screen; retained boundary uncertainty is not process capability."""
import argparse
import hashlib
import json
from pathlib import Path

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--out', type=Path, required=True)
a = p.parse_args()
a.out.mkdir(parents=True, exist_ok=False)
source = Path('validation/sole_retention_decision_v1/report.json')
e = json.loads(source.read_text())['boundary_error_each_mm']
# Dimensions of build_sole_recessed_seat.py. Do not silently reduce e to pass.
quantities = {
    'seat_thickness': 1.6,
    'yoke_roof_thickness': 2.0,
    'seat_to_channel_radial_gap': 3.8 - 3.21,
    'channel_end_wall': 47 - (35 + 8 + 3.8),
}
rows = [{ 'quantity': name, 'nominal_mm': value,
          'minimum_under_boundary_assumption_mm': value - 2 * e }
        for name, value in quantities.items()]
result = {
    'boundary_error_each_mm': e,
    'basis': 'Previous Codex boundary-position assumption, not validated print accuracy',
    'rows': rows,
    'finding': 'Channel end wall can disappear under retained uncertainty; do not rely on it for retention or print as an intentional thin wall.',
    'strength_qualified': False,
    'next_design_action': 'Compare deliberate open-ended relief against relocation; verify load-bearing roof and clamped seat rather than relying on end wall.',
    'sources': {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in [source, Path('software/sim/structural/build_sole_recessed_seat.py')]},
}
(a.out / 'report.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(rows))
