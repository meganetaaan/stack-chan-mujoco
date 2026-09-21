"""Conditional voltage budget, not an electrical protection certification."""
import hashlib
import json
from pathlib import Path

out = Path('validation/branch_regen_diode_review_v1')
plan = json.loads((out / 'plan.json').read_text())
brake_path = Path('validation/brake_51ohm_envelope_faults_v1/report.json')
wire_path = Path('validation/servo_wire_selection_v1/report.json')
brake = json.loads(brake_path.read_text())
wire = json.loads(wire_path.read_text())
current = wire['evaluation_current_A']
if current != 1:
    raise ValueError('Selected diode specification is for 1 A only')
vf = 0.275  # PMEG3050EP, Table 7, IF=1 A, Tj=25 C, maximum
wire_drop = wire['nominal_wire_plus_post_environment_contact_drop_V']
limit = plan['criteria']['servo_terminal_max_V']
rows = []
for name, values in brake['cases'].items():
    total = values['bus_max_V'] + vf + wire_drop
    rows.append({'archived_brake_state': name,
                 'branch_protection_state': 'open; reverse diode conducting',
                 'conditional_terminal_budget_V': total,
                 'remaining_to_6V_V': limit - total,
                 'arithmetic_screen_pass': total <= limit})
report = {
    'candidate': 'PMEG3050EP across branch protection; anode downstream, cathode common bus',
    'comparison_current_A': current,
    'diode_vf_max_at_1A_25C_V': vf,
    'wire_and_contacts_comparison_drop_V': wire_drop,
    'maximum_bus_budget_at_this_comparison_V': limit - vf - wire_drop,
    'rows': rows,
    'decision': 'Do not promote this combination to manufacturing BOM',
    'electrical_protection_verified': False,
    'source_sha256': {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in (brake_path, wire_path, out / 'plan.json')},
}
(out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
