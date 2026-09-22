"""Choose a nominal ramp capacitor while keeping unsupported current/thermal claims open."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
p=argparse.ArgumentParser()
p.add_argument('--tab5-pdf',type=Path,required=True)
p.add_argument('--tps-pdf',type=Path,required=True)
a=p.parse_args()
# The reviewed PDF is external source data, not redistributed with this calculation.
expected='13cf3fd9954d39aa198e57b1bb94ec56af7d49107c80a245acc5bd90ac8ea329'
assert hashlib.sha256(a.tab5_pdf.read_bytes()).hexdigest()==expected
assert hashlib.sha256(a.tps_pdf.read_bytes()).hexdigest()=='b781cbce51984715771bde540df2b36404b4fae4b41e27166c84c19b6598e1de'
src=ROOT/'schematics/power/protected_pack_system_candidate_v6/assembly.json'
r=json.loads(src.read_text());parts={x['reference']:x for x in r['parts']}
assert parts['TAB5__U_PROTECT']['part']=='TPS26601RHFR'
assert parts['TAB5__U_PROTECT']['pins']['13'] is None
assert parts['TAB5__C_DVDT']['value_F'] is None
# Reuse an already selected C0G 100nF/50V nominal part; no DC-bias model invented.
assert parts['TAB5__C_PROTECT_OUT_1']['part']=='GRM31C5C1H104JA01L'
assert parts['TAB5__C_PROTECT_OUT_1']['value_F']==1e-7
internal_C=2*10e-6+100e-9
external_C=sum(parts[n]['value_F'] for n in ['TAB5__C_PROTECT_OUT_1','TAB5__C_PROTECT_OUT_2'])
cap=100e-9
slope_eq1=4.7e-6*24.6/cap
slope_eq2=1/(8e3*cap)
report={
 'decision':'Select100nF ramp capacitor for detailed design; not startup/protection qualification',
 'selected_part':{'reference':'TAB5__C_DVDT','part':'GRM31C5C1H104JA01L','value_F':cap,
                  'basis':'Reuse existing selected nominal100nF part; limits inherited from existing capacitor selection'},
 'current_limit_resistor':None,
 'other_branch_mode_review':{
  'SYS__U_LOGIC_PROTECT':{'MODE':parts['SYS__U_LOGIC_PROTECT']['pins']['13'],
   'part':parts['SYS__U_LOGIC_PROTECT']['part'],'R_ILIM_ohm':parts['SYS__R_LOGIC_ILIM']['value_ohm'],
   'nominal_breaker_threshold_A':12000/parts['SYS__R_LOGIC_ILIM']['value_ohm']+.03,
   'continuous_clamp':False},
  'U_CTRL_INPUT_LIMIT':{'MODE_net':parts['U_CTRL_INPUT_LIMIT']['pins']['13'],
   'MODE_resistor_part':parts['R_CTRL_INPUT_MODE']['part'],
   'response':'402kohm-to-RTN active-current-limit with latch; do not conflate with SYS/Tab5 MODE-open'}},
 'verified_schematic_facts':{
  'path':['J9 pin2 SYS_VIN','D7 DSK36','FU4 marked1A/30V resettable','U21 MP4560DN VIN'],
  'return':'J9 pin1 GND',
  'nominal_input_caps':[{'ref':'C101','F':10e-6,'V':50},{'ref':'C102','F':10e-6,'V':50},{'ref':'C85','F':100e-9,'V':50}],
  'FU4_exact_part':None,'FU4_trip_curve':None,
  'connector':'J9 HEADER_2X5; not the supplied1.25mm6pin RS485 cable'},
 'mode_decision':{
  'MODE':'open','response':'circuit breaker with latch-off, retained',
  'nominal_ICB_formula':'12000/R_ILIM_ohm +0.03 A',
  'not_a_continuous_current_clamp':True,
  'active_limit_latch_alternative':'402kohm MODE-to-RTN; not adopted, fault energy and startup remain unqualified',
  'MODE_direct_RTN_is_auto_retry':'Do not short MODE to RTN when latch-off is required'},
 'cap_only_nominal_comparison':{
  'internal_nominal_F':internal_C,'external_nominal_F':external_C,
  'combined_for_comparison_F':internal_C+external_C,
  'eq1_slope_V_s':slope_eq1,'eq2_approx_slope_V_s':slope_eq2,
  'eq1_charging_current_A':(internal_C+external_C)*slope_eq1,
  'eq2_approx_charging_current_A':(internal_C+external_C)*slope_eq2,
  'ramp_rows':[{'vin_V':v,'eq1_ramp_s':v/slope_eq1,'eq2_approx_ramp_s':v/slope_eq2} for v in [9.,12.6]],
  'scope':'Diode conducting and capacitors following common ramp, no converter load; nominal illustration, not inrush bound'},
 'engineering_reason':'A populated slow-ramp component gives a controllable first design point; capacitive-only nominal demand is tens of mA. Do not enlarge capacitance repeatedly without assessing converter startup and eFuse heating.',
 'stop_condition':'One schematic reconciliation and nominal ramp calculation; next solve startup load/thermal/harness envelope before R_ILIM selection',
 'unresolved':['Actual board revision correspondence','Capacitance tolerance/bias/temperature and distributed input network',
  'MP4560 startup/operating current, downstream startup and peak waveform',
  'Connector/contact/harness current rating and FU4 part/trip/derating',
  'ICB tolerance at chosen R, fast-trip overshoot and delay, 3S applicability',
  'Output ramp min/max and startup power/energy/thermal behavior',
  'OFF detection and residual energy; slow ramp does not implement5second restart rule'],
 'sources':[
  {'url':'https://m5stack-doc.oss-cn-shenzhen.aliyuncs.com/1132/Tab5_Schematics_PDF.pdf','sha256':expected,'pages':[4,5]},
  {'url':'https://www.ti.com/lit/ds/symlink/tps2660.pdf','sha256':hashlib.sha256(a.tps_pdf.read_bytes()).hexdigest(),'revision':'SLVSDG2G','pages':[7,8,9,21,22,23,30,31]},
 ],
 'source_sha256':{str(src.relative_to(ROOT)):hashlib.sha256(src.read_bytes()).hexdigest()},
 'manufacturing_release':False,'startup_verified':False,
}
out=ROOT/'schematics/power/tab5_startup_parameter_candidate_v1';out.mkdir(exist_ok=True)
(out/'selection.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report['cap_only_nominal_comparison'],indent=2))
