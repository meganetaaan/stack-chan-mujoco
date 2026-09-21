"""Bounded static design screen; no IC transient model or total preload claim."""
import argparse
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[3]
parser = argparse.ArgumentParser()
parser.add_argument('--out', type=Path, required=True)
a = parser.parse_args()
paths = ['schematics/power/logic_predischarge_inhibit_candidate.json',
         'schematics/power/logic_supply_candidate.json',
         'schematics/power/system_power_integration_candidate_v1/assembly.json']
d = [json.loads((root / p).read_text()) for p in paths]
inhibit, logic, assembly = d
parts = {p['reference']: p for p in assembly['parts']}
assert parts[inhibit['target_reference']]['pins'][inhibit['target_pin']] == inhibit['net']
assert parts['SYS__R_LOGIC_SHDN_PD']['pins']['2'] == 'PACK_RETURN'
# +/-1% is an allocated TOTAL resistor variation, not qualification of the PCB.
tol = 0.01
rd = inhibit['pulldown']['ohm']
rs = inhibit['series']['ohm']
load = logic['continuous_design_target_A']
report = {
 'source_sha256': {p: hashlib.sha256((root / p).read_bytes()).hexdigest() for p in paths},
 'resistor_total_variation_allocation': tol,
 'pull_down_sink_at_0_4V_min_A': 0.4 / (rd * (1 + tol)),
 'datasheet_sink_requirement_A_at_0_4V': 10e-6,
 'high_drive_min_assumed_V': 3.0,
 'high_SHDN_min_ignoring_internal_pullup_V': 3.0 * rd*(1-tol)/(rd*(1-tol)+rs*(1+tol)),
 'high_drive_load_at_3_6V_max_ignoring_internal_pullup_A': 3.6/((rd+rs)*(1-tol)),
 'host_not_selected_and_partial_power_not_qualified': True,
 'rejected_combination': {
   'classification': 'conditional incompatibility with existing design load budget, not measured behavior',
   'logic_continuous_design_target_A': load,
   'illustrative_precharge_R_ohm': 100,
   'candidate_stop_delta_V': 0.5,
   'logic_alone_steady_voltage_drop_V': 100*load,
   'strict_R_upper_bound_ohm_logic_alone': 0.5/load,
   'steady_load_limit_A_for_100ohm': 0.5/100,
   'claim': 'Cannot accept 100ohm while allowing this load during precharge; equality gives only asymptotic arrival',
 },
 'still_on_or_unknown_during_predischarge': [
   'STOP_AUX3V3 branch including LDO, monitors, pullups and charge current',
   'TPS26601 input quiescent current, dividers and 100k input bleed',
   'Both disabled Pololu regulators: typical shutdown current is not a guaranteed maximum',
   'Pololu input capacitors, eFuse input/output leakage and downstream backfeed',
   'BQ PACK/LD sensing and load-detection state; PDSG hardware',
   'Unimplemented Tab5 input branch, inhibit and USB/backfeed policy',
   'Unimplemented cross-domain driver loading and all startup capacitor currents',
 ],
 'logic_branch_off_leakage_guaranteed_A': None,
 'whole_predischarge_load_bound_A': None,
 'precharge_R_selected_ohm': None,
 'electrical_qualification': False,
 'manufacturing_release': False,
}
assert report['pull_down_sink_at_0_4V_min_A'] > 10e-6
assert report['high_SHDN_min_ignoring_internal_pullup_V'] > 1.0
a.out.mkdir(parents=True, exist_ok=True)
(a.out/'report.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report, indent=2))
