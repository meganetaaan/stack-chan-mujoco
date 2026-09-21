"""Integrate reviewed logic supply candidates without changing the released/current pointer."""
import argparse,copy,csv,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--include-stop-cap-candidate',action='store_true');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
paths={'base':'schematics/power/servo_power_clear_pullup_candidate_v1/assembly.json','branch':'schematics/power/logic_input_branch_candidate_v1/branch.json','ldo':'schematics/power/logic_supply_candidate.json'}
if a.include_stop_cap_candidate:paths['stop_cap']='schematics/power/stop_output_capacitor_requirements.json'
data={k:json.loads(Path(v).read_text()) for k,v in paths.items()};base=data['base'];branch=data['branch'];ldo=data['ldo'];assembly=copy.deepcopy(base)
new=[]
ic=branch['ic'];new.append({'reference':ic['ref'],'part':ic['part'],'pins':{n:s['net'] for n,s in ic['pins'].items()},'pin_dispositions':ic['pins'],'source':paths['branch']})
for item in branch['resistors']+branch['capacitors']:
 c=copy.deepcopy(item);c['reference']=c.pop('ref');c['source']=paths['branch'];new.append(c)
new.append({'reference':'U_LOGIC_LDO','part':ldo['part'],'pins':ldo['pins'],'source':paths['ldo'],'note':ldo['enable']})
cap=ldo['output_capacitor_candidate'];new.append({'reference':'C_LOGIC_LDO_OUT','part':cap['part'],'value_F':cap['nominal_F'],'pins':{'1':'LOGIC3V3','2':'GND'},'source':paths['ldo'],'qualification':cap})
assembly['parts']+=new
assembly['scope']='Combined logic supply and R14 candidate with revM protection; electrical/PCB qualification incomplete.'
assembly['manufacturing_release']=False
assembly['interfaces']['LOGIC3V3']='Driven by U_LOGIC_LDO; current, startup and capacitor stability remain unqualified'
assembly['interfaces']['BATTERY_RAW']='Shared source feeding logic and STOP branches; battery, UBEC inputs, source disconnect and backfeed not integrated'
assembly['candidate_integration']={'inputs':paths,'source_sha256':{k:hashlib.sha256(Path(v).read_bytes()).hexdigest() for k,v in paths.items()},'current_pointer_changed':False,'missing':['Battery and converter complete models','MCU startup sequencer and receivers','Output capacitor stability qualification','Current thresholds for 118kohm and 3S','Integrated startup/fault/thermal/PCB verification','Shared source discharge/backfeed bound'],'forbidden_net_merges':branch['forbidden_net_merges']}
refs=[c['reference'] for c in assembly['parts']];assert len(refs)==len(set(refs)), 'Duplicate reference'
assert assembly['parts'][:len(base['parts'])]==base['parts'], 'Base circuit changed'
changes=[]
if a.include_stop_cap_candidate:
 selected=data['stop_cap'];target=next(c for c in assembly['parts'] if c['reference']=='C_STOP_OUT')
 assert target['part'] is None and target['value_F']==selected['candidate']['nominal_F']
 before=copy.deepcopy(target)
 target['part']=selected['candidate']['part_number']
 target['selection_source']=paths['stop_cap'];target['qualification']=copy.deepcopy(selected)
 changes.append({'reference':'C_STOP_OUT','before':before,'after':copy.deepcopy(target),'change':'Ordering candidate only; value and pins unchanged; stability remains unqualified'})
 assembly['candidate_integration']['base_overlays']=changes
 assert all(c==b for c,b in zip(assembly['parts'],base['parts']) if c['reference']!='C_STOP_OUT')
prot=new[0]['pins'];assert prot['15']==prot['EP'] and prot['15']!=prot['17']
assert prot['23']==prot['24']==ldo['pins']['6']
assert ldo['pins']['1']=='LOGIC3V3'
assert all(r['pins']['2']=='LOGIC_PROTECT_RTN' for r in branch['resistors'] if r['ref'] in ['R_LOGIC_UV_BOTTOM','R_LOGIC_OV_BOTTOM','R_LOGIC_ILIM'])
assert len([c for c in new if c['reference']=='R_LOGIC_INPUT_BLEED'])==1
report={'base_parts':len(base['parts']),'added_parts':len(new),'total_parts':len(refs),'numbered_and_EP_pin_entries':sum(len(c['pins']) for c in assembly['parts']),'added_references':[c['reference'] for c in new],'checks':{'unique_references':True,'base_parts_unchanged':not changes,'base_overlay_count':len(changes),'all_other_base_parts_unchanged':True,'RTN_separate_from_GND':True,'protection_to_LDO_connected':True,'logic_rail_connected':True},'electrical_qualification':False,'check_scope':'Connectivity assembly only; no semiconductor behavior, ERC, transient or layout claim'}
report['unselected_references']=[c['reference'] for c in assembly['parts'] if not c.get('part')]
report['all_part_numbers_assigned']=not report['unselected_references']
(a.out/'assembly.json').write_text(json.dumps(assembly,indent=2)+'\n');(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
with (a.out/'candidate_bom.csv').open('w') as f:
 w=csv.writer(f,lineterminator='\n');w.writerow(['reference','part','status'])
 for c in assembly['parts']:w.writerow([c['reference'],c.get('part'),'candidate_not_released' if c.get('part') else 'unselected'])
print(json.dumps(report,indent=2))
