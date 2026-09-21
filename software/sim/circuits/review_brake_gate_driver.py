"""Limited DC compatibility screen; no dynamic or fault protection approval."""
import json
from pathlib import Path

p = Path('validation/brake_gate_driver_review_v1')
plan = json.loads((p/'plan.json').read_text())
criteria, assumptions = plan['criteria'], plan['assumptions']
rmin = json.loads(Path('validation/brake_51ohm_envelope_faults_v1/plan.json').read_text())['Rmin_ohm']
# Ignore other series resistance for an upper comparison current bound.
imax = assumptions['bus_upper_V'] / rmin
source_rise = imax * assumptions['source_shunt_ohm']
vg = assumptions['driver_test_supply_V'] - assumptions['driver_high_drop_max_V_at_10mA']
report = {
    'startup_drop_budget_V': criteria['normal_bus_min_V']-criteria['driver_start_max_V'],
    'comparison_source_rise_V': source_rise,
    'comparison_Vgs_at_datasheet_output_test_V': vg-source_rise,
    'comparison_margin_to_2_5V_V': vg-source_rise-criteria['gate_comparison_min_V'],
    'supply_choice': 'load-side servo bus, driver ground at bus ground',
    'aux_supply_dependency_removed_for_driver_only': True,
    'comparator_and_reference_dependency_removed': False,
    'electrical_protection_verified': False,
}
(p/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
