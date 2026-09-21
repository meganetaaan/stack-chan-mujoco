"""Carry selected bypass capacitors into the current assembly; leave bulk/gate parts alone."""
import argparse,csv,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
base=Path('schematics/power/servo_power_rearm_integration_revJ/assembly.json')
spec=Path('schematics/power/manual_rearm_capacitors.json')
r=json.loads(base.read_text());s=json.loads(spec.read_text())
refs=[f'C{i}' for i in range(1,12)]+['C14','C15','LEFT_C_WINDOW','RIGHT_C_WINDOW','C_MONITOR_START','C_MONITOR_RX']
changed=[]
for part in r['parts']:
 if part['reference'] not in refs:continue
 assert set(part['pins'].values()) in ({'LOGIC3V3','GND'},{'STOP_AUX3V3','GND'})
 assert part.get('value_F',1e-7)==1e-7
 changed.append({'reference':part['reference'],'previous_part':part['part']})
 part.update(part=s['part_number'],value_F=s['nominal_capacitance_F'],selection_source=str(spec))
assert len(changed)==17
r['scope']='Integrate existing 100 nF bypass selection at 17 additional references'
r['source_sha256']={str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in (base,spec,Path(__file__))}
r['integration_limitations'].append('Local 100nF capacitors now have ordering candidates; bulk and gate capacitors remain unselected. PCB return inductance and full rail stability not qualified.')
a.out.mkdir(parents=True,exist_ok=False)
(a.out/'assembly.json').write_text(json.dumps(r,indent=2)+'\n')
(a.out/'selection_report.json').write_text(json.dumps({'changed':changed,'total_same_part_count':sum(x['part']==s['part_number'] for x in r['parts']), 'unchanged_part_count':len(r['parts']), 'nominal_voltage_screen_V':3.6,'rated_voltage_V':s['rated_voltage_V'], 'voltage_rating_screen_pass':3.6<s['rated_voltage_V'],'high_frequency_decoupling_verified':False,'regulator_stability_verified':False,'manufacturing_release':False},indent=2)+'\n')
with (a.out/'candidate_bom.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['reference','part_candidate','value_F','value_ohm'])
 for x in r['parts']:w.writerow([x['reference'],x['part'],x.get('value_F',''),x.get('value_ohm','')])
print('17 capacitor selections integrated; total 21 of this candidate; bulk/gate unchanged')
