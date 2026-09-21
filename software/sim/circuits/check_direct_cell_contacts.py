"""Necessary voltage and travel conditions for one specified battery-contact pair.

Not a transient model, battery discharge curve, or force-sharing model.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--out', type=Path, required=True)
a = p.parse_args()
a.out.mkdir(parents=True, exist_ok=False)
spec_path = ROOT / 'validation/direct_cell_contact_gate_v1/contact_spec.json'
budget_path = ROOT / 'validation/direct_cell_voltage_budget_v1/report.json'
cell_path = ROOT / 'validation/direct_cell_p2150r_v1/cell_candidate.json'
spec, budget, cell = [json.loads(x.read_text()) for x in (spec_path, budget_path, cell_path)]
row = next(x for x in budget['rows'] if x['shared_current_comparison_A'] == 4.917 and x['axis'] == 'XC330-M288-T')
# Contacts precede the left/right split: they carry BOTH leg currents.
current = 2 * row['shared_current_comparison_A']
results = []
for label, resistance in spec['resistance_per_contact_ohm'].items():
    drop = current * 2 * resistance
    needed = row['necessary_loaded_source_V_before_other_losses'] + drop
    results.append({'contact_condition': label, 'pair_drop_V': drop,
                    'pair_loss_W': current * drop,
                    'necessary_loaded_battery_V_before_unbudgeted_losses': needed,
                    'remaining_at_4p2V_before_unbudgeted_losses_V': cell['voltage_V']['maximum'] - needed})
# Sum-of-compressions is only necessary: force equilibrium and individual travel
# still need checking. The battery length minimum is deliberately not invented.
h = spec['free_height_mm']
cmin, cmax = spec['vertical_compression_mm']
gap_low = 2*(h['nominal']+h['tolerance']) - 2*cmax
gap_high = 2*(h['nominal']-h['tolerance']) - 2*cmin
r = {'source_sha256': {str(x.relative_to(ROOT)): hashlib.sha256(x.read_bytes()).hexdigest() for x in (spec_path,budget_path,cell_path)},
     'comparison_total_current_A': current, 'contact_current_rating_A_at_25C': spec['current_rating_A_at_25C'],
     'electrical_comparison': results,
     'necessary_PCB_spacing_minus_battery_length_interval_mm': [gap_low,gap_high],
     'remaining_total_spacing_and_battery_length_tolerance_width_mm': gap_high-gap_low,
     'battery_length_min_mm': None,
     'fixed_holder_travel_verified': False,
     'decision': 'not_selected_for_direct_cell_holder',
     'limits': ['14A is specified at 25C ambient, not all operating temperatures.',
                'Contact resistance conditions are not established for this battery terminal finish.',
                'Existing 4.917A per-leg eFuse resistance comparison is outside its 3A tabulated test condition.',
                'Battery sag, fuse, STOP switch, wires, PCB and remaining connections still consume voltage.',
                'Travel interval is a necessary aggregate condition, not individual spring compression/force proof.',
                'No claim that all possible contacts or the single-cell architecture are infeasible.'],
     'manufacturing_release': False}
(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps(r,indent=2))
