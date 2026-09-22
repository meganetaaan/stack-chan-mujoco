"""Preserve rejected v3; condition MCU reset-release RC with a Schmitt buffer."""
import copy
import csv
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
source = ROOT / 'schematics/power/protected_pack_system_candidate_v3/assembly.json'
out = ROOT / 'schematics/power/protected_pack_system_candidate_v4'
validation = ROOT / 'validation/sequence_clear_input_v1'
for directory in (out, validation):
    directory.mkdir(exist_ok=True)
a = json.loads(source.read_text())
r = copy.deepcopy(a)
p = {x['reference']: x for x in r['parts']}
assert len(p) == 194
assert p['IF_CLEAR__U_OD']['part'] == 'SN74LVC1G07DBVR'
assert p['IF_CLEAR__U_OD']['pins']['2'] == 'CTRL_RESET_RELEASE_N'
assert p['IF_CLEAR__R_INPUT_PU']['value_ohm'] == 10000
p['IF_CLEAR__U_OD']['pins']['2'] = 'CTRL_RESET_RELEASE_CONDITIONED'
p['IF_CLEAR__R_INPUT_PU']['placement'] = 'At Schmitt input, pulled to CTRL3V3 when MCU is high impedance'
r['parts'].extend([
    {'reference': 'IF_CLEAR__U_SCHMITT', 'part': '74LVC1G17GV',
     'pins': {'1': None, '2': 'CTRL_RESET_RELEASE_N', '3': 'PACK_RETURN',
              '4': 'CTRL_RESET_RELEASE_CONDITIONED', '5': 'CTRL3V3'},
     'integration_group': 'sequence_clear_interface'},
    {'reference': 'IF_CLEAR__C_SCHMITT', 'part': 'GRM31C5C1H104JA01L',
     'value_F': 1e-7, 'pins': {'1': 'CTRL3V3', '2': 'PACK_RETURN'},
     'placement': 'At Schmitt buffer supply',
     'integration_group': 'sequence_clear_interface'},
])
old = {x['reference']: x for x in a['parts']}
new = {x['reference']: x for x in r['parts']}
changed = [ref for ref in old if old[ref]['pins'] != new[ref]['pins']]
assert changed == ['IF_CLEAR__U_OD']
assert len(new) == len(r['parts']) == 196
r['checks'].pop('unique194references')
r['checks'].update(unique196references=True, prior_pin_maps_changed=changed)
r['status'] = 'sequence_clear_schmitt_candidate_not_operational'
r['source_sha256'] = {str(source.relative_to(ROOT)): hashlib.sha256(source.read_bytes()).hexdigest()}
sources = [
    {'url': 'https://www.ti.com/lit/ds/symlink/sn74lvc1g07.pdf',
     'revision': 'AG October2025', 'sections': ['5.3 input edge10ns/V', '5.5 input capacitance4pF typical']},
    {'url': 'https://assets.nexperia.com/documents/data-sheet/74LVC1G17.pdf',
     'revision': '16.1 September2024', 'sections': ['2 unlimited input rise/fall', '6 GV pinout', '7 noninverting truth table']},
    {'url': 'https://assets.nexperia.com/documents/data-sheet/74LVC1G07.pdf',
     'revision': '18 September2024', 'sections': ['9 edge limit10ns/V despite introductory Schmitt wording']},
]
# Diagnostic at nominal values: no added MCU/trace capacitance or leakage.
# Average slope over valid input thresholds avoids assuming a 10%-90% convention.
vcc, resistance, capacitance, vil, vih = 3.3, 10000, 4e-12, .8, 2.
delta_t = resistance * capacitance * math.log((vcc-vil)/(vcc-vih))
rate = delta_t / (vih-vil)
assert rate > 10e-9
report = {
    'source_sha256': r['source_sha256'], 'sources': sources,
    'rejected_candidate': 'protected_pack_system_candidate_v3',
    'case': 'CTRL3V3 stable3.3V; previously low MCU PA4 becomes high impedance',
    'engineering_comparison': {'R_ohm': resistance, 'VCC_V': vcc,
       'C_F': capacitance, 'C_status': 'TI typical input only, not guaranteed maximum',
       'MCU_and_trace_capacitance_included': False, 'leakage_included': False,
       'VIL_V': vil, 'VIH_V': vih, 'threshold_window_time_ns': delta_t*1e9,
       'threshold_window_average_ns_per_V': rate*1e9,
       'manufacturer_limit_ns_per_V': 10,
       'capacitance_for_average_limit_pF': capacitance*10e-9/rate*1e12},
    'decision': 'Reject direct10k-to-SN74LVC1G07 as qualified design; nominal typical-capacitance comparison already exceeds limit, not proof every specimen fails',
    'correction': 'Add74LVC1G17GV and100nF on CTRL3V3; preserve clear polarity and OD isolation',
    'alternative_rejected': 'Nexperia74LVC1G07 also specifies10ns/V; Schmitt action wording does not remove requirement',
    'termination_condition': 'Stop RC refinement of rejected input. Next close conditioned output edge/DC/load and power sequence behavior before approval.',
    'remaining': ['Schmitt output edge into OD input with bounded pin/trace capacitance',
       'MCU reset pad state/leakage and Schmitt threshold margins',
       'Output1k pullup and AUP input edge/leakage with new driver',
       'Full reset fanout, cold start, brownout and asynchronous rail loss',
       'CTRL current and capacitance budgets include new two buffers and pullup'],
    'electrically_qualified': False, 'manufacturing_release': False,
}
r['sequence_clear_interface']['input_conditioning'] = report
r['sequence_clear_interface']['limits'].extend(report['remaining'])
r['sequence_clear_interface']['sources'].extend(sources[1:])
(out/'assembly.json').write_text(json.dumps(r, indent=2)+'\n')
(validation/'report.json').write_text(json.dumps(report, indent=2)+'\n')
for name, header, rows in [
    ('bom.csv', ['reference','part','group'], [[x['reference'],x.get('part'),x.get('integration_group')] for x in r['parts']]),
    ('connections.csv', ['reference','pin','net'], [[x['reference'],pin,net] for x in r['parts'] for pin,net in x['pins'].items()]),
]:
    with (out/name).open('w', newline='') as f:
        w = csv.writer(f, lineterminator='\n'); w.writerow(header); w.writerows(rows)
print(json.dumps({'references':len(new), 'old_input_average_ns_per_V':rate*1e9,
                  'changed_prior_pin_maps':changed, 'qualified':False}))
