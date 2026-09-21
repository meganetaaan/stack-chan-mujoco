"""Add a separate low-current stop-supply input branch; no servo-current protection implied."""
import argparse,json,hashlib
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
base=Path('schematics/power/servo_power_rearm_integration_revK/assembly.json');r=json.loads(base.read_text())
for x in r['parts']:
 for pin,net in x['pins'].items():
  if net=='BATTERY_REVERSE_PROTECTED':x['pins'][pin]='STOP_LDO_INPUT'
r['parts'] += [
 {'reference':'R_STOP_INPUT','part':'TNPW12061K00BYEA','value_ohm':1000,'total_tolerance_budget':.01,'pins':{'1':'BATTERY_RAW','2':'STOP_INPUT_LIMITED'},'placement':'At battery branch entry before any downstream copper exposed to a short'},
 {'reference':'D_STOP_REVERSE','part':'BAS116','ordering_suffix_pending':True,'pins':{'1':'STOP_INPUT_LIMITED','2':None,'3':'STOP_LDO_INPUT'},'placement':'SOT23: pin1 anode, pin3 cathode, pin2 NC'},
 {'reference':'R_STOP_INPUT_BLEED','part':'TNPW0603100KBYEA','value_ohm':100000,'total_tolerance_budget':.01,'pins':{'1':'STOP_LDO_INPUT','2':'GND'}}]
r['interfaces'].pop('BATTERY_REVERSE_PROTECTED',None)
r['interfaces']['BATTERY_RAW']='Dedicated low-current stop branch from battery; battery/main servo protection not included; common return GND'
r['interfaces']['STOP_LDO_INPUT']='After 1k resistor and BAS116; 100k bleed. Startup, reverse transient and exact diode order qualification pending'
r['part_count']=len(r['parts']);r['pin_count']=sum(len(x['pins']) for x in r['parts'])
r['scope']=__doc__;r['source_sha256']={str(base):hashlib.sha256(base.read_bytes()).hexdigest()}
r['integration_limitations'].append('Low-current input resistor/diode/bleed added. Does not qualify hot polarity reversal, resistor bypass/short failure, battery cell protection, input transients or upstream wiring shorts.')
a.out.mkdir(parents=True,exist_ok=False)
(a.out/'assembly.json').write_text(json.dumps(r,indent=2)+'\n')
# Selection screen uses existing load comparison; do not promote it to a guarantee.
load=json.loads(Path('validation/stop_supply_budget_v1/report.json').read_text())['conditional_DC_sum_A']
report={'sources':['https://assets.nexperia.com/documents/data-sheet/BAS116.pdf','https://www.vishay.com/docs/28758/tnpw_e3.pdf'],
 'fixed_comparison_conditions':{'battery_max_V':12.6,'battery_low_V':9,'ambient_C':85,'diode_drop_assumed_V':1,'series_total_tolerance':.01,'load_evidence':'validation/stop_supply_budget_v1/report.json'},
 'short_current_max_A':12.6/990,'series_short_power_W':12.6**2/990,
 'series_general_mode_derated_W':.27*(125-85)/(125-70),
 'reverse_steady_leakage_only_V':80e-9*101000,
 'low_battery_LDO_input_comparison_V':9-1-1010*(load+12.6/99000),
 'remaining':['9V low battery is a comparison, not chosen cell cutoff',
 'BAS116 drop limit is a pulsed 25C test at 10mA; use at actual current/temperature unresolved',
 '80nA reverse leakage limit specified at 75V and 150C; application comparison only',
 'Reverse leakage calculation excludes transient capacitive coupling and other backfeed',
 'Regulator ground current and dynamic charge not in load comparison',
 'Resistor film temperature, accumulated drift and PCB layout unqualified'],
 'part_count':r['part_count'],'pin_count':r['pin_count'],'qualification':False}
assert report['series_short_power_W']<report['series_general_mode_derated_W']
(a.out/'screen.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
