"""Separate injected regeneration from sustained converter-fault absorption."""
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
paths=[Path('schematics/power/brake_resistor_candidate.json'),Path('validation/disconnect_regeneration_v1/plan.json')]
brake,regen=[json.loads(x.read_text()) for x in paths]
vlimit=6.;vstart=5.25
pulse=regen['pulse_s'][1]-regen['pulse_s'][0]
# Charge conservation for the old constant-current test; not an EPIC4 energy bound.
charge=regen['regeneration_A']*pulse
cap_required=charge/(vlimit-vstart)
rmin=brake['resistance_ohm']*(1-brake['tolerance_fraction'])
rmax=brake['resistance_ohm']*(1+brake['tolerance_fraction'])
report={'sources_sha256':{str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in paths},
 'requirements':{'servo_max_V':vlimit,'normal_max_comparison_V':vstart,'change_to_original_limits':False},
 'regeneration_stress_case':{'current_A':regen['regeneration_A'],'duration_s':pulse,'charge_C':charge,'proven_robot_regeneration_bound':False,
 'capacitor_only_min_F_for_constant_current_no_other_load':cap_required,'assumed_old_capacitance_F':960e-6,
 'energy_accepted_at_voltage_ceiling_J':vlimit*charge},
 'resistor_screen':{'resistance_ohm':[rmin,rmax],
 'one_branch_current_at_6V_ideal_switch_A':[vlimit/rmax,vlimit/rmin],
 'two_branches_total_max_at_6V_ideal_switch_A':2*vlimit/rmin,
 'one_branch_power_at_6V_W':[vlimit*vlimit/rmax,vlimit*vlimit/rmin],
 'continuous_rating_P70_W':brake['P70_W'],'complete_thermal_qualification':False},
 'decision':'Retain resistor only as an unqualified regeneration candidate; do not count it as protection against sustained battery feedthrough.',
 'architecture_constraints':['LEFT_SERVO_BUS and RIGHT_SERVO_BUS require load-side absorption on each isolated bus; do not join buses to reuse the historical common-brake design.',
 'Battery feedthrough needs upstream interruption or series regulation plus bounded transient energy; a 4.7ohm branch cannot sink arbitrary battery current.',
 'Motor regeneration after source cutoff needs absorption still powered from the affected load-side bus.',
 'Per-servo disconnect can isolate a motor from the leg absorber; this must remain in the fault scope.'],
 'limits':['1A stress injection is inherited Codex test input, not a measured or model-derived physical worst case.',
 'Resistor calculation assumes a fully on ideal switch, no shunt or wiring resistance, no inductive delay, and initial tolerance only.',
 'P70 is not a safe printed-enclosure operating power; mounting, temperature and pulse/repetition limits remain unqualified.',
 'The actual battery fault current and interruption time are not bounded by normal actuator load or eFuse nominal current settings.'],
 'qualified':False}
a.out.mkdir(parents=True,exist_ok=False);(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
