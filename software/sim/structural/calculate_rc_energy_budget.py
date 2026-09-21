"""Conditional 100-second walking energy budget; no measured runtime claim."""
import argparse
import hashlib
import json
from pathlib import Path
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--out', type=Path, required=True)
a = p.parse_args()
a.out.mkdir(parents=True, exist_ok=False)
pack_path = Path('schematics/power/rc_supply_candidate.json')
load_path = Path('validation/model_dc_envelope_v2/report.json')
pack = json.loads(pack_path.read_text())
load = json.loads(load_path.read_text())
duration = 10 / 0.10
voltage = pack['regulator']['selected_setting_V']
servo_power = voltage * load['robot_draw_upper_A']
ideal_energy = servo_power * duration / 3600
nominal_energy = pack['battery']['nominal_voltage_V'] * pack['battery']['capacity_Ah']
# Only one documented efficiency comparison, not an invented parameter sweep.
eta_comparison = 0.90
comparison_energy = ideal_energy / eta_comparison
report = {
    'planning_duration_s': duration,
    'duration_basis': '10m at target threshold 0.10m/s; planning point, not new maximum duration',
    'model_servo_power_W': servo_power,
    'ideal_servo_energy_Wh': ideal_energy,
    'pack_nominal_energy_Wh': nominal_energy,
    'efficiency_comparison': {
        'value': eta_comparison,
        'source': 'https://hobbywing.oss-cn-shenzhen.aliyuncs.com/pdf/pdfen/UBEC10A2-6S.pdf',
        'status': 'Manufacturer efficiency statement without operating-condition bound; not guaranteed minimum',
        'servo_battery_energy_Wh': comparison_energy,
        'fraction_of_nominal_pack_energy': comparison_energy / nominal_energy,
    },
    'budget_equation': 'E_usable_Wh >= 1.3658333333333332/eta + P_aux_battery_W/36 + E_other_Wh',
    'definitions': {
        'E_usable_Wh': 'Energy deliverable before qualified per-cell cutoff, including load, temperature and pack age',
        'eta': 'Guaranteed energy-weighted conversion efficiency for the actual servo branch profile, including distribution loss',
        'P_aux_battery_W': 'Average battery-side Tab5 and control power over the 100-second planning interval',
        'E_other_Wh': 'Additional startup/shutdown energy outside that interval and explicitly chosen reserve, without double-counting',
    },
    'sources_sha256': {str(f): hashlib.sha256(f.read_bytes()).hexdigest() for f in [pack_path, load_path]},
    'limitations': ['Conditional ideal bridge load envelope, not qualified hardware DC maximum',
                    'Nominal battery Wh is not usable energy',
                    'No claim of 20 trials on one charge',
                    'Current pulses, thermal limits, wiring and protection remain separate constraints'],
    'qualified': False,
}
(a.out/'report.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report['efficiency_comparison']))
