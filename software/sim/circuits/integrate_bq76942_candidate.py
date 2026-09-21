"""Compose selected candidate fragments; unresolved pins remain explicit."""
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
power=ROOT/'schematics/power'
sources=['bq76942_candidate.json','bq76942_series_filter_candidate.json','bq76942_pack_fet_candidate.json']
a,c,q=[json.loads((power/s).read_text()) for s in sources]
parts=[]
def add(ref,part,pins,**extra):
 parts.append({'reference':ref,'part':part,'pins':{str(k):v for k,v in pins.items()},**extra})
bq_pins={str(p['pin']):p['sense_net'] for p in a['cell_input_map']['pins']}
bq_pins.update({'17':'CELL_B_MINUS','43':'BQ76942_DSG_43','45':'BQ76942_CHG_45'})
for pin in a['cell_input_map']['NC_pins_left_open']:bq_pins[str(pin)]=None
unresolved=[i for i in range(1,49) if str(i) not in bq_pins]
add('U_CELL_PROTECT',a['part'],bq_pins,unresolved_pins=unresolved)
for ref,pins in q['pin_connections'].items():add(ref,q['part'],pins)
g=q['gate_network_candidate']
for x in g['connections']:
 suffix=x['FET'][2:]
 add('R_GATE_'+suffix,g['series_resistor']['part'],dict(enumerate(x['series_resistor'],1)))
 add('R_GS_'+suffix,g['gate_source_resistor']['part'],dict(enumerate(x['bleed_resistor'],1)))
 add('D_GS_'+suffix,g['zener']['type'],x['zener_pins'],ordering_suffix_pending=True)
for i,b in enumerate(a['cell_input_filter_candidate']['branches']):
 add(f'R_CELL_{i}',a['cell_input_filter_candidate']['resistor']['part'],dict(enumerate(b['resistor'],1)))
for f in c['filters']:
 for x in f['capacitors']:add(x['reference'],c['capacitor_part'],dict(enumerate(x['nets'],1)))
assert len(parts)==37 and len({p['reference'] for p in parts})==37
# Check that the obsolete 8-capacitor parallel-only filter was not also imported.
assert sum(p['part']==c['capacitor_part'] for p in parts)==24
out=power/'battery_protection_integration_candidate_v1';out.mkdir(exist_ok=True)
assembly={'status':'partial_connection_candidate','parts':parts,'part_count':len(parts),'unresolved_BQ76942_pins':unresolved,'source_sha256':{s:hashlib.sha256((power/s).read_bytes()).hexdigest() for s in sources},'external_ports':['CELL_B_MINUS','CELL1_TAP','CELL2_TAP','CELL3_TAP','CELL_POS_FUSED','PACK_POS_PROTECTED'],'missing_stages':['cell tap and main connectors','battery fuse and reverse protection','shunt and current filters','BAT REG18 CP1 and optional LDO supply','PACK and LD input network','configuration and startup inhibit','temperature inputs and protection settings','system/servo integration'],'electrically_operational':False,'manufacturing_release':False}
(out/'assembly.json').write_text(json.dumps(assembly,indent=2)+'\n')
with (out/'bom.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['part_or_type','quantity','references'])
 for part,n in sorted(Counter(p['part'] for p in parts).items()):w.writerow([part,n,' '.join(p['reference'] for p in parts if p['part']==part)])
with (out/'connections.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['reference','pin','net','status'])
 for p in parts:
  for pin,net in p['pins'].items():w.writerow([p['reference'],pin,net,'NC' if net is None else 'candidate_connected'])
  for pin in p.get('unresolved_pins',[]):w.writerow([p['reference'],pin,'','UNRESOLVED'])
print(f'{len(parts)} parts; {len(unresolved)} BQ pins unresolved; not operational')
