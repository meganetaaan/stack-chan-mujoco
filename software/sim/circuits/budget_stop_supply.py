"""Connectivity-backed conditional DC load budget; does not qualify transients."""
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--assembly',type=Path);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
source=a.assembly or Path(json.loads(Path('schematics/power/servo_power_rearm_current.json').read_text())['assembly'])
r=json.loads(source.read_text());parts={x['reference']:x for x in r['parts']}
vhi=3.393;vlo=3.207
refs={k for k,v in parts.items() if 'STOP_AUX3V3' in v['pins'].values()}
caps={k for k in refs if k.startswith('C') or '_C_' in k}
resistors={'R8':100000,'R_STOP_MIN_LOAD':30100,'LEFT_R_WINDOW_PULLUP':10000,'RIGHT_R_WINDOW_PULLUP':10000,'R_MONITOR_START':100000}
ics={'U9':6e-6,'U10':6e-6,'U_MONITOR_START':6e-6,'U11':4e-6,'LEFT_U_WINDOW':13e-6,'RIGHT_U_WINDOW':13e-6}
ov_drivers=[side+'_U_OV_DRIVE' for side in ['LEFT','RIGHT'] if side+'_U_OV_DRIVE' in parts]
for ref in ov_drivers:ics[ref]=10e-6
assert refs==caps|set(resistors)|set(ics)|{'U_STOP_LDO'}, 'Unbudgeted rail endpoint: revise budget'
rows=[]
for ref,value in resistors.items():
 x=parts[ref];assert x['pins']['1']=='STOP_AUX3V3'
 if 'value_ohm' in x:assert x['value_ohm']==value
 rows.append({'reference':ref,'comparison_A':vhi/(value*.99),'basis':'Full rail across resistor, total tolerance assumed +/-1%; R8 exact selection pending'})
for ref,current in ics.items():rows.append({'reference':ref,'comparison_A':current,'basis':'Published supply-current test point extended to rail range; see limitations'})
rows += [{'reference':'U10 MR internal pullup','comparison_A':vhi/70000,'basis':'MR at 0V, 70kohm minimum; current sourced by U10 rail, not a second independent U11 output load'},
 {'reference':'U_MONITOR_START SENSE','comparison_A':1.7e-6,'basis':'Fixed SENSE current limit measured at 6.5V, comparison at 3.393V'},
 {'reference':'U10 SENSE','comparison_A':25e-9,'basis':'G01 limit measured near VIT, not validated at rail'},
 {'reference':'U11 additional input supply current','comparison_A':500e-6,'basis':'VI=VCC-0.6V test point; not a bound for arbitrary slow ramps'}]
for ref in ov_drivers:
 side=ref.split('_')[0]
 hi=parts[side+'_R_OV_TOP'];lo=parts[side+'_R_OV_BOTTOM']
 assert parts[ref]['pins']['4']==hi['pins']['1'] and hi['pins']['2']==lo['pins']['1'] and lo['pins']['2']=='GND'
 rows += [
  {'reference':ref+' divider drive','comparison_A':vhi/((hi['value_ohm']+lo['value_ohm'])*.99)+.1e-6,'basis':'Output-sourced resistor load plus OVLO leakage comparison'},
  {'reference':ref+' additional input supply current','comparison_A':500e-6,'basis':'VI=VCC-0.6V test point, not an arbitrary-ramp bound'}]
load=sum(x['comparison_A'] for x in rows)
# LDO ground current at 150mA is not established here as a maximum over load.
pass_power=(12.6-vlo)*load
report={'assembly':str(source),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
 'rail_endpoints_accounted':sorted(refs),'capacitors_excluded_from_DC_sum':sorted(caps),
 'load_rows':rows,'conditional_DC_sum_A':load,'minimum_load_resistor_only_A':vlo/(30100*1.01),
 'pass_element_only_power_W':pass_power,'JEDEC_theta_JA_K_W':212.1,
 'pass_element_only_temperature_rise_K':pass_power*212.1,
 'qualified_total_current':False,'qualified_thermal_result':False,
 'limits':['Regulator ground-pin dissipation not included in pass-element result',
 'Actual PCB thermal resistance and ambient not established',
 'TPS3808 supply limits tested with reset unasserted; reset-state/internal-current coverage unresolved',
 'TPS3700 limits at listed supply points; continuous rail and loaded-output coverage unresolved',
 'U11 extra current at one input voltage does not bound an arbitrary input ramp',
 'Capacitor leakage, capacitor charge/discharge, dynamic switching and board leakage excluded',
 'LOGIC3V3-powered R9 and source divider currents are deliberately not charged to STOP_AUX3V3',
 'Not all summed load maxima must occur together; this is a conservative component-budget comparison only'],
 'decision':'Retain TPS70933 candidate for now; no known DC-load sizing reason to increase rating, but qualification remains incomplete'}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ('conditional_DC_sum_A','pass_element_only_power_W','pass_element_only_temperature_rise_K')},indent=2))
