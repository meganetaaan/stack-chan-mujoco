"""Check actual logic-branch resistor candidates against the existing 1% allocation."""
import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--out', type=Path, required=True)
args = parser.parse_args()
args.out.mkdir(parents=True, exist_ok=True)
branch = json.loads(Path('schematics/power/logic_input_branch_candidate_v1/branch.json').read_text())
# Criteria fixed before evaluation: 1% allocation, TPS2660 5.36k..120k.
rows = []
for r in branch['resistors']:
    s = r['selection']
    dt = max(abs(t - 25) for t in s['film_temperature_C'])
    tolerance = s['initial_tolerance']
    drift = s['tcr_ppm_per_K'] * 1e-6 * dt
    low = (1 - tolerance) * (1 - drift)
    high = (1 + tolerance) * (1 + drift)
    budget = s['total_design_allocation']
    row = {'ref': r['ref'], 'part': r['part'],
           'initial_plus_temperature_ohm': [r['value_ohm'] * low, r['value_ohm'] * high],
           'allocated_ohm': [r['value_ohm'] * (1-budget), r['value_ohm'] * (1+budget)],
           'remaining_fraction_for_process_and_age': min(low-(1-budget), (1+budget)-high),
           'initial_temperature_within_allocation': low >= 1-budget and high <= 1+budget}
    if r['ref'] == 'R_LOGIC_ILIM':
        row['allocated_range_within_IC_recommended'] = 5360 <= row['allocated_ohm'][0] and row['allocated_ohm'][1] <= 120000
        # Datasheet nominal equation only: this is NOT a guaranteed threshold range.
        row['nominal_IOL_A'] = 12000 / r['value_ohm']
        row['nominal_IOL_change_from_120k_percent'] = (120000/r['value_ohm']-1)*100
    rows.append(row)
report = {'criteria': {'total_allocation_fraction': .01, 'ILIM_recommended_ohm': [5360,120000]},
          'rows': rows, 'qualified': False,
          'limitations': ['Film temperature -40..125C is an engineering envelope, not verified PCB temperature',
                         'Process and aging must fit remaining allocation; not yet qualified',
                         '120k datasheet current threshold limits are not transferred to 118k',
                         'No startup, fault, thermal, availability or full-board qualification']}
(args.out/'report.json').write_text(json.dumps(report, indent=2)+'\n')
assert all(r['initial_temperature_within_allocation'] for r in rows)
assert all(r.get('allocated_range_within_IC_recommended', True) for r in rows)
print(json.dumps(report, indent=2))
