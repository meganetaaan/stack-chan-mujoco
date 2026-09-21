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
bq_pins.update({'17':'CELL_B_MINUS','43':'BQ76942_DSG_43','45':'BQ76942_CHG_45','41':'BQ_LD','42':'BQ_PACK','47':'BQ_BAT_HOLD','24':'BQ_REG18','46':'BQ_CP1','18':'BQ_SRP','20':'BQ_SRN'})
for pin in a['cell_input_map']['NC_pins_left_open']:bq_pins[str(pin)]=None
# Unused optional functions, per datasheet Table16-3; not silicon NC.
unused_open=[28,31,32,34,35,38]
for pin in unused_open:bq_pins[str(pin)]=None
for pin in [36,37]:bq_pins[str(pin)]='CELL_B_MINUS'
unresolved=[i for i in range(1,49) if str(i) not in bq_pins]
add('U_CELL_PROTECT',a['part'],bq_pins,unresolved_pins=unresolved,intentionally_unused_open_pins=unused_open,disabled_LDO_required=True)
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
# Separate sense resistors preserve the distinct PACK and LD functions.
add('R_LD','TNPW060310K0BEEA',{1:'PACK_POS_PROTECTED',2:'BQ_LD'})
add('R_PACK','TNPW060310K0BEEA',{1:'PACK_POS_PROTECTED',2:'BQ_PACK'})
add('R_BAT','TNPW1206100RBEEA',{1:'CELL_POS_FUSED',2:'BQ_BAT_DIODE_A'})
add('D_BAT','BAS116',{1:'BQ_BAT_DIODE_A',2:None,3:'BQ_BAT_HOLD'},ordering_suffix_pending=True)
add('C_BAT','C1206C105K3RACTU',{1:'BQ_BAT_HOLD',2:'CELL_B_MINUS'},effective_capacitance_qualified=False)
for i in range(3):
 add(f'C_REG18_{i}','C1206C105K3RACTU',{1:'BQ_REG18',2:'CELL_B_MINUS'},effective_capacitance_qualified=False)
add('C_CP1','C1206C105K3RACTU',{1:'BQ_CP1',2:'BQ_BAT_HOLD'},effective_capacitance_qualified=False)
add('R_SHUNT','WSLP25125L000FEA',{1:'CELL_B_MINUS',2:'PACK_RETURN'},kelvin_routing_required=True,thermal_qualified=False)
add('R_SRP','TNPW0603100RBEEA',{1:'CELL_B_MINUS',2:'BQ_SRP'})
add('R_SRN','TNPW0603100RBEEA',{1:'PACK_RETURN',2:'BQ_SRN'})
add('C_CURRENT','C1206C104J3GACAUTO',{1:'BQ_SRP',2:'BQ_SRN'})
assert len(parts)==50 and len({p['reference'] for p in parts})==50
# Check that the obsolete 8-capacitor parallel-only filter was not also imported.
assert sum(p['part']==c['capacitor_part'] and p['reference'].startswith('C_F') for p in parts)==24
out=power/'battery_protection_integration_candidate_v1';out.mkdir(exist_ok=True)
assembly={'status':'partial_connection_candidate','parts':parts,'part_count':len(parts),'unresolved_BQ76942_pins':unresolved,'source_sha256':{s:hashlib.sha256((power/s).read_bytes()).hexdigest() for s in sources},'external_ports':['CELL_B_MINUS','CELL1_TAP','CELL2_TAP','CELL3_TAP','CELL_POS_FUSED','PACK_POS_PROTECTED','PACK_RETURN'],'missing_stages':['cell tap and main connectors','battery fuse and reverse protection','current threshold, shunt thermal/pulse and sense-routing qualification','BAT hold-up and input faults; REG18/CP1 effective capacitance and startup; optional LDO supply','PACK/LD transient and reverse-polarity qualification','configuration and startup inhibit','temperature inputs and protection settings','system/servo integration'],'electrically_operational':False,'manufacturing_release':False}
(out/'assembly.json').write_text(json.dumps(assembly,indent=2)+'\n')
with (out/'bom.csv').open('w') as f:
 w=csv.writer(f,lineterminator='\n');w.writerow(['part_or_type','quantity','references'])
 for part,n in sorted(Counter(p['part'] for p in parts).items()):w.writerow([part,n,' '.join(p['reference'] for p in parts if p['part']==part)])
with (out/'connections.csv').open('w') as f:
 w=csv.writer(f,lineterminator='\n');w.writerow(['reference','pin','net','status'])
 for p in parts:
  for pin,net in p['pins'].items():w.writerow([p['reference'],pin,net,('UNUSED_OPEN' if int(pin) in p.get('intentionally_unused_open_pins',[]) else 'NC') if net is None else 'candidate_connected'])
  for pin in p.get('unresolved_pins',[]):w.writerow([p['reference'],pin,'','UNRESOLVED'])
print(f'{len(parts)} parts; {len(unresolved)} BQ pins unresolved; not operational')
