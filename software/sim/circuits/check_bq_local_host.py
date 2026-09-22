"""Check package allocation and integrated BQ host connectivity; not firmware proof."""
import argparse
import hashlib
import json
from pathlib import Path
root = Path(__file__).resolve().parents[3]
p = argparse.ArgumentParser(); p.add_argument('--out', type=Path, required=True); a = p.parse_args()
paths = ['schematics/power/bq_local_host_candidate.json', 'schematics/power/system_power_integration_candidate_v1/assembly.json']
host, assembly = [json.loads((root / x).read_text()) for x in paths]
parts = {x['reference']: x for x in assembly['parts']}
u = parts['BAT__U_BQ_HOST']['pins']; bq = parts['BAT__U_CELL_PROTECT']['pins']
checks = {
 'all_20_package_pins_disposed': set(u) == {str(i) for i in range(1,21)},
 'sda_pin1_pb7_to_bq27': u['1'] == bq['27'] == 'BQ_SDA',
 'scl_pin20_pb6_to_bq26': u['20'] == bq['26'] == 'BQ_SCL',
 'i2c_separate_package_pins': u['1'] != u['20'],
 'host_on_pre_main_fet_reg1': u['4'] == bq['35'] == 'BQ_CTRL3V3',
 'host_reference_bminus': u['5'] == bq['17'] == 'CELL_B_MINUS',
 'alert_pa2_pin9': u['9'] == bq['25'] == 'BQ_ALERT_N',
 'allow_pa0_via_gate_and_series_inhibit': u['7'] == parts['BAT__U_BQ_MAIN_GATE']['pins']['1'] and parts['BAT__U_BQ_MAIN_GATE']['pins']['4'] == parts['BAT__R_ALLOW_SER']['pins']['1'],
 'nrst_and_debug_not_enable_outputs': [u[k] for k in ['6','18','19']] == ['BQ_HOST_NRST','BQ_HOST_SWDIO','BQ_HOST_SWCLK'],
 'sda_bonded_pb8_inactive': 'PB8' in host['pin_allocation']['1']['inactive_bonded_gpios'],
 'scl_bonded_others_inactive': set(host['pin_allocation']['20']['inactive_bonded_gpios']) == {'PB3','PB4','PB5'},
 'aux_cross_domain_not_directly_wired': u['8'] != 'SYS__LOGIC_START_ALLOW',
}
assert all(checks.values()), checks
report = {'source_sha256':{x:hashlib.sha256((root/x).read_bytes()).hexdigest() for x in paths},
 'checks':checks,'scope':'Package pin and named-net inspection only. GPIO initialization, currents, levels, reset and fault timing not verified.',
 'system_part_count':len(parts),'host_local_parts_added':len(host['parts']),
 'host_operating_supply_V':[2.0,3.6],'BQ_REG1_conditional_supply_V':[3.0,3.6],
 'supply_range_overlap_only':True,'supply_startup_qualified':False,
 'firmware_implemented':False,'fault_gate_connected':True,'independent_fault_cutoff_qualified':False,'manufacturing_release':False}
a.out.mkdir(parents=True,exist_ok=True)
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
