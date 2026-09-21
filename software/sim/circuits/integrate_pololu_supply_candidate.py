"""Connect selected modules through functional ports; preserve unqualified protection circuit."""
import argparse,copy,csv,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
files={'base':'schematics/power/servo_power_logic_integration_candidate_v2/assembly.json','module':'schematics/power/dual_pololu_candidate.json','interface':'schematics/power/dual_pololu_interface.json'}
d={k:json.loads(Path(v).read_text()) for k,v in files.items()};base=d['base'];spec=d['interface'];aout=copy.deepcopy(base);new=[]
for side in ['LEFT','RIGHT']:
 pins={port:(cfg['net_pattern'].format(SIDE=side) if 'net_pattern' in cfg else cfg['net']) for port,cfg in spec['ports_each'].items()}
 new.append({'reference':side+'_U_REGULATOR','part':d['module']['part'],'manufacturer':'Pololu','manufacturer_item':5671,'pins':pins,'pin_key_semantics':'functional signals only; not physical pad numbering','source':files['interface'],'physical_pad_mapping_verified':False})
aout['parts']+=new
assert aout['parts'][:len(base['parts'])]==base['parts']
refs=[p['reference'] for p in aout['parts']];assert len(refs)==len(set(refs))
byref={p['reference']:p for p in aout['parts']}
for side in ['LEFT','RIGHT']:
 pins=byref[side+'_U_REGULATOR']['pins'];assert pins['VOUT']==byref[side+'_U_POWER']['pins']['5']==side+'_REGULATOR_OUT'
 assert pins['VIN']=='DRIVE_BATTERY_PROTECTED' and pins['GND']=='GND'
 assert all(pins[p] is None for p in ['ENA','ENB','PFM','PG'])
 assert pins['VOUT']!=side+'_SERVO_BUS'
assert new[0]['pins']['VOUT']!=new[1]['pins']['VOUT']
aout['scope']='Pololu functional-port connection candidate added to existing logic/protection; not a manufacturing netlist or qualified power system'
aout['part_count']=len(refs);aout['pin_count']=sum(len(p['pins']) for p in aout['parts']);aout['functional_module_ports']=14
aout['interfaces']['DRIVE_BATTERY_PROTECTED']='Required protected/switched3S drive source, shared by regulator VIN; upstream source/disconnect/fuse not integrated'
aout['interfaces']['BATTERY_RAW']='Logic and STOP raw source branches; relation to protected drive source, battery isolation and source return routing remain unfinished'
for side in ['LEFT','RIGHT']:aout['interfaces'][side+'_REGULATOR_OUT']='Driven by '+side+'_U_REGULATOR VOUT; thermal/dropout/transient behavior unqualified'
aout['candidate_integration']={'inputs':files,'source_sha256':{k:hashlib.sha256(Path(v).read_bytes()).hexdigest() for k,v in files.items()},'base_part_entries_unchanged':True,'current_pointer_changed':False,'required_but_unproven':spec['required_but_unproven']}
aout['logical_composition_only']=True;aout['electrical_qualification']=False;aout['manufacturing_release']=False
report={'base_parts':len(base['parts']),'added_modules':len(new),'total_parts':len(refs),'base_pin_entries':sum(len(p['pins']) for p in base['parts']),'added_functional_ports':14,'total_connection_entries':aout['pin_count'],'checks':{'base_parts_unchanged':True,'unique_references':True,'outputs_not_paralleled':True,'own_efuse_input_connection':True,'no_direct_servo_bus_connection':True,'optional_ports_explicitly_unconnected':True,'module_PG_not_merged_with_efuse_PG':True},'check_scope':'Functional connectivity only; no ERC, physical pad map, startup/off-state behavior, protection simulation or firmware validation','empty_part_fields':[p['reference'] for p in aout['parts'] if not p.get('part')],'nonempty_part_field_does_not_guarantee_ordering_code_or_qualification':True,'manufacturing_release':False}
(a.out/'assembly.json').write_text(json.dumps(aout,indent=2)+'\n');(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
with (a.out/'candidate_bom.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['reference','part','status'])
 for p in aout['parts']:w.writerow([p['reference'],p.get('part'),'candidate_not_released' if p.get('part') else 'unselected'])
print(json.dumps(report,indent=2))
