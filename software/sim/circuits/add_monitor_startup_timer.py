"""Add a dedicated monitor startup timer; verify conditional timing, not fault coverage."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--out', type=Path, required=True)
a = p.parse_args()
base = Path('schematics/power/servo_power_rearm_integration_revF/assembly.json')
r = copy.deepcopy(json.loads(base.read_text()))
new = [
    {'reference': 'U_MONITOR_START', 'part': 'TPS3808G33DBVR',
     'pins': {'1': 'MONITOR_START_READY_OD', '2': 'GND', '3': 'STOP_AUX3V3',
              '4': None, '5': 'STOP_AUX3V3', '6': 'STOP_AUX3V3'}},
    {'reference': 'R_MONITOR_START', 'part': None, 'value_ohm': 100000,
     'pins': {'1': 'STOP_AUX3V3', '2': 'MONITOR_START_READY_OD'}},
    {'reference': 'C_MONITOR_START', 'part': None, 'value_F': 100e-9,
     'pins': {'1': 'STOP_AUX3V3', '2': 'GND'}},
]
assert not ({x['reference'] for x in new} & {x['reference'] for x in r['parts']})
r['parts'] += new
parts = {x['reference']: x for x in r['parts']}
for side in ('LEFT', 'RIGHT'):
    assert parts[side + '_U_WINDOW']['pins']['5'] == new[0]['pins']['6']
assert new[0]['pins']['4'] is None
assert all(net not in ('MAIN_EFUSE_EN', 'RESET_N')
           for x in new for net in x['pins'].values())
r['scope'] = __doc__
r['part_count'] = len(r['parts'])
r['pin_count'] = sum(len(x['pins']) for x in r['parts'])
r['source_sha256'] = {str(base): hashlib.sha256(base.read_bytes()).hexdigest(),
                       __file__: hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
r['interfaces']['MONITOR_START_READY_OD'] = (
    'Startup-delay evidence only. Receiver, startup inhibition and short-dip invalidation '
    'not implemented. Never direct enable or complete source-valid status.')
r['integration_limitations'] += [
    'TPS3808G33 startup delay added; downstream qualification/sequencer not implemented',
    'Short supply dips and undefined low-supply outputs are not covered by the timer proof',
    'Timer output load must meet datasheet timing conditions; receiver and exact passives pending',
]
r['manufacturing_release'] = False
r['electrical_qualification'] = False
# Use the larger threshold as hysteresis percentage basis, conservatively.
vit_min, vit_max = 3.07 * .985, 3.07 * 1.015
release_max = vit_max * 1.025
aux_min = 3.207  # Existing LDO comparison, not a measured or fully qualified rail.
report = {
    'part_count': r['part_count'], 'pin_count': r['pin_count'],
    'classification': 'conditional_datasheet_bound_comparison_not_transient_simulation',
    'derived_design_requirement': 'No power permission based on invalid monitor state',
    'manufacturer_constraints': {
        'supervisor': {'source': 'https://www.ti.com/lit/ds/symlink/tps3808.pdf',
                       'revision': 'SBVS050N August 2026', 'pages': [3, 4, 6, 7],
                       'falling_threshold_V': [vit_min, vit_max],
                       'hysteresis_max_fraction': .025,
                       'CT_open_delay_s': [.012, .028],
                       'timing_load': '100 kohm, 50 pF; VDD 1.7..6.5 V; -40..125 C',
                       'sense_pulse_condition_s': 20e-6,
                       'sense_pulse_levels': 'High 1.05 VIT, Low 0.95 VIT'},
        'monitor': {'source': 'https://www.ti.com/lit/ds/symlink/tps3700.pdf',
                    'revision': 'SBVS187G February 2019', 'page': 6,
                    'startup_max_s': .000450, 'continuous_supply_min_V': 1.8}},
    'design_assumptions': ['Common local supply at both monitor and timer pins',
                           'Monotonic initial ramp followed by continuous valid supply',
                           'Timer delay output loading satisfies datasheet conditions',
                           'STOP_AUX minimum 3.207 V is an existing conditional LDO budget'],
    'bounds': {'release_threshold_conservative_max_V': release_max,
               'conditional_rail_release_margin_V': aux_min - release_max,
               'minimum_wait_minus_monitor_startup_s': .012 - .000450,
               'timer_start_threshold_above_monitor_min_V': vit_min - 1.8},
    'conditional_initial_startup_check': (aux_min > release_max and .012 > .000450
                                          and vit_min > 1.8),
    'not_proven': ['Receiver logic levels and capacitance',
                   'Inhibition during POR and arbitrary supply ramps',
                   'Detection of sub-20 us dips; no invented minimum actual dip duration',
                   'Requalification after every monitor-invalidating dip',
                   'Maximum complete fault-to-power-off delay and energy',
                   'Complete startup sequencer and fresh manual restart'],
    'electrical_qualification': False, 'manufacturing_release': False,
}
a.out.mkdir(parents=True, exist_ok=False)
(a.out / 'assembly.json').write_text(json.dumps(r, indent=2) + '\n')
(a.out / 'integration_report.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'parts': r['part_count'], 'pins': r['pin_count'], 'bounds': report['bounds'],
                  'conditional_initial_startup_check': report['conditional_initial_startup_check']}))
