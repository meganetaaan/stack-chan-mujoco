"""Reconcile partial startup probe allocations with integrated v4; no full-load claim."""
import hashlib
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT/'validation/controller_probe_load_v1'
OUT.mkdir(exist_ok=True)
paths = {
 'assembly': 'schematics/power/protected_pack_system_candidate_v4/assembly.json',
 'main': 'validation/main_allow_interface_screen_v1/report.json',
 'aux': 'validation/aux_start_connection_v1/report.json',
 'old_assembly': 'schematics/power/pack_control_ramp_candidate_v1/assembly.json',
}
data = {k: json.loads((ROOT/v).read_text()) for k,v in paths.items()}
parts = {x['reference']:x for x in data['assembly']['parts']}
assert len(parts)==196
# Check actual new loads are still on the relevant rails/ports.
assert parts['IF_CLEAR__R_INPUT_PU']['pins']=={'1':'CTRL3V3','2':'CTRL_RESET_RELEASE_N'}
assert parts['IF_CLEAR__R_INPUT_PU']['part']=='TNPW060310K0BEEA'
assert parts['IF_CLEAR__U_SCHMITT']['part']=='74LVC1G17GV'
assert parts['IF_CLEAR__U_OD']['part']=='SN74LVC1G07DBVR'
assert parts['IF_CLEAR__U_SCHMITT']['pins']['5']==parts['IF_CLEAR__U_OD']['pins']['5']=='CTRL3V3'
assert parts['IF_MAIN__R_INPUT_PD']['pins']['1']=='MAIN_START_ALLOW'
assert parts['CTRL__U_AUX_GATE']['pins']['4']=='SYS__LOGIC_START_ALLOW'
additions = [
 {'name':'aux_permission_branch', 'A':data['aux']['calculations']['CTRL_high_extra_branch_current_A_at3_6V'], 'basis':'Inherited conditional10uA SHDN leakage allocation, not a full range guarantee'},
 {'name':'clear_input_pullup', 'A':3.6/(10000*.99), 'basis':'Engineering3.6V,1% total resistance envelope, node low'},
 {'name':'clear_OD_static_ICC', 'A':10e-6, 'basis':'TI SN74LVC1G07 RevAG5.5 catalog rail-input static condition'},
 {'name':'clear_Schmitt_static_ICC', 'A':4e-6, 'basis':'Nexperia74LVC1G17 Rev16.1 table7 catalog input condition'},
 {'name':'clear_OD_input_leakage', 'A':5e-6, 'basis':'TI input leakage magnitude allocation charged to driving CTRL rail'},
 {'name':'clear_Schmitt_input_leakage', 'A':1e-6, 'basis':'Nexperia input leakage allocation; may overlap pullup budget, retained conservatively'},
]
rows = [{'MCU_MHz':x['MCU_MHz'], 'partial_screen_sum_A':x['partial_screen_sum_A']+sum(y['A'] for y in additions)} for x in data['main']['updated_partial_controller_budgets']]
def caps(assembly):
 return {p['reference']:p['value_F'] for p in assembly['parts'] if p['reference'].split('__')[-1].startswith('C_') and set(p['pins'].values())=={'CTRL3V3','PACK_RETURN'}}
current_caps, old_caps = caps(data['assembly']), caps(data['old_assembly'])
added_caps = {k:v for k,v in current_caps.items() if k not in old_caps}
assert added_caps=={'IF_CLEAR__C_HF':1e-7, 'IF_CLEAR__C_SCHMITT':1e-7}
report = {
 'source_sha256':{v:hashlib.sha256((ROOT/v).read_bytes()).hexdigest() for v in paths.values()},
 'rows':rows, 'added_to_main_interface_partial_budget':additions,
 'CTRL3V3_nominal_capacitors_F':current_caps,
 'CTRL3V3_nominal_capacitance_F':sum(current_caps.values()),
 'added_nominal_capacitance_F':sum(added_caps.values()),
 'SYS_clear_output_pullup_current_charged_to_CTRL':False,
 'SYS_clear_output_pullup_note':'SYS__R14 is supplied by SYS__LOGIC3V3. OD sinks this current but it is not CTRL LDO output current.',
 'sources':['https://www.ti.com/lit/ds/symlink/sn74lvc1g07.pdf','https://assets.nexperia.com/documents/data-sheet/74LVC1G17.pdf'],
 'limits':['Inherited MCU characterized peripheral-disabled current and resistor envelopes retained; not simultaneous actual state',
 'Static IC catalog conditions do not bound intermediate inputs or switching;500uA deltaICC at one test point is not an all-input maximum',
 'Existing logic/supervisor missing consumption, IO/debug loads, MCU enabled peripherals, capacitor tolerance/leakage and LDO ground current remain',
 'Nominal capacitors only; no voltage bias/temperature/tolerance qualification',
 'Full rail maximum remains unknown; equivalent resistor is only a reproducible probe'],
 'total_controller_max_current_A':None, 'qualified':False, 'manufacturing_release':False,
}
(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'partial64MHz_A':rows[-1]['partial_screen_sum_A'], 'nominal_output_capacitance_F':sum(current_caps.values()), 'added_caps':added_caps}))
