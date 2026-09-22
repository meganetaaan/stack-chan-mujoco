"""Compare real Schmitt receiver leakage and partial-power limits before integration."""
import argparse
import json
from pathlib import Path

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--out',type=Path,required=True)
a=p.parse_args()
base=Path('schematics/power/servo_power_rearm_integration_revG/assembly.json')
parts={x['reference']:x for x in json.loads(base.read_text())['parts']}
assert parts['R_MONITOR_START']['value_ohm']==100000
assert parts['U_MONITOR_START']['pins']['1']=='MONITOR_START_READY_OD'
rows=[]
for vendor,part,leak,off,url,revision in [
 ('Nexperia','74LVC1G17GV',1e-6,2e-6,'https://assets.nexperia.com/documents/data-sheet/74LVC1G17.pdf','16.1, 2024-09-03'),
 ('TI','SN74LVC1G17DBVR',5e-6,10e-6,'https://www.ti.com/lit/ds/symlink/sn74lvc1g17.pdf','SCES351Y, October 2025')]:
 rows.append({'manufacturer':vendor,'part':part,'source':url,'revision':revision,
  'input_leakage_spec_A':leak,'Ioff_spec_A':off,
  'conditional_input_high_min_V':3.207-(leak+300e-9)*101000,
  'conditional_output_off_with_100k_pulldown_V':off*101000,
  'input_threshold_guaranteed_for_entire_3V207_to_3V393_interval':False,
  'qualification':False})
r={'scope':__doc__,'rows':rows,
 'assumptions':['100 kohm resistor total +/-1 percent; exact resistor unselected',
                'Existing conditional STOP_AUX lower bound 3.207 V',
                'TPS3808 released-output leakage upper 300 nA applied to operating point',
                'Input leakage specified at 0 or 5.5 V used as operating-point comparison',
                'Output-off estimate excludes downstream leakage and applies at VCC=0 only'],
 'decision':'Prefer Nexperia for further receiver design because of lower leakage; do not integrate as qualified',
 'reason_not_qualified':'Both datasheets list Schmitt thresholds at discrete VCC values; no interpolation used as a guaranteed bound across actual rail interval',
 'proposed_receiver':{'part':'74LVC1G17GV','pins':{'1':None,'2':'MONITOR_START_READY_OD','3':'GND','4':'MONITOR_START_READY_LOGIC','5':'LOGIC3V3'},
   'output_pulldown_ohm':100000,'bypass_F':100e-9},
 'fault_cases':[
  {'case':'STOP_AUX valid, LOGIC3V3 zero','finding':'Input tolerates powered source; output high impedance plus Ioff, not actively Low; external pulldown required'},
  {'case':'LOGIC3V3 between zero and recommended minimum','finding':'Ioff at VCC=0 does not guarantee behavior across ramp; separate inhibition required'},
  {'case':'Both rails valid','finding':'Leakage budget calculated; thresholds and actual capacitance still require closure'},
  {'case':'STOP_AUX short dip','finding':'Buffer cannot restore lost timer qualification; revG limitation remains'}],
 'next_design_exit_conditions':['Guaranteed receiver input levels across selected supply range',
   'Worst total input capacitance/loading compatible with TPS3808 delay specification',
   'Actual inhibition path valid throughout partial supply ramps; no reliance on Ioff away from zero'],
 'manufacturing_release':False}
a.out.mkdir(parents=True,exist_ok=False)
(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps(rows,indent=2))
