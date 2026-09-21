"""Enumerate directly rail-connected resistor loads without claiming a full rail budget."""
import argparse,hashlib,json,re
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
path=Path('schematics/power/servo_power_clear_pullup_candidate_v1/assembly.json');data=json.loads(path.read_text())
# Explicit known ordering-code values, not a generic part-number decoder.
values={'TNPW0603150KBYEA':150000,'TNPW060310K0BYEA':10000}
plan={'scope':'Direct LOGIC3V3 and STOP_AUX3V3 resistor branches only. Non-rail terminal clamped to 0 V for simultaneous conditional upper subtotal.', 'rail_max_V':3.393,'assumed_total_resistance_tolerance':.01,'limits':['Not a realistic simultaneous operating state or complete rail upper bound.','IC supply currents, output-driven resistors, internal button pullup, capacitive transients, MCU and board leakage excluded.','1% is an engineering allocation including resistors whose exact parts remain unselected.','No negative-voltage fault currents covered.'], 'stop':'One inventory extraction and subtotal; no unknown-IC simulation.'}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');rails={}
for rail in ['LOGIC3V3','STOP_AUX3V3']:
 rows=[];other=[]
 for x in data['parts']:
  if rail not in x['pins'].values():continue
  if not (re.match(r'^R[0-9_]',x['reference']) or '_R_' in x['reference'] or re.match(r'(LEFT|RIGHT)_R\d',x['reference'])):
   other.append({'reference':x['reference'],'part':x['part'],'connected_pins':[k for k,v in x['pins'].items() if v==rail]});continue
  assert len(x['pins'])==2
  value=x.get('value_ohm',values.get(x['part']))
  source='assembly value or explicit ordering-code mapping'
  if value is None:
   m=re.match(r'([0-9.]+)k\b',x['part']);assert m,x
   value=float(m[1])*1000;source='unselected nominal value in assembly description'
  rows.append({'reference':x['reference'],'resistance_ohm':value,'value_source':source,'other_net':next(v for v in x['pins'].values() if v!=rail),'conditional_current_upper_A':3.393/(value*.99)})
 rails[rail]={'direct_resistors':rows,'conditional_resistor_subtotal_A':sum(r['conditional_current_upper_A'] for r in rows),'other_connected_parts_not_budgeted':other}
result={'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'rails':rails,'complete_current_budget':False,'manufacturing_release':False}
(a.out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:{'resistors':len(v['direct_resistors']),'subtotal_mA':v['conditional_resistor_subtotal_A']*1000,'other_parts':len(v['other_connected_parts_not_budgeted'])} for k,v in rails.items()},indent=2))
