"""Package the current manual-rearm candidate and explicit unfinished interfaces."""
import argparse,csv,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--supervisor',action='store_true');p.add_argument('--en-driver',action='store_true');p.add_argument('--en-clamp',action='store_true');p.add_argument('--clamp-cause',action='store_true');p.add_argument('--permission-gate',action='store_true');p.add_argument('--pg-receiver',action='store_true');a=p.parse_args();
if a.pg_receiver and not a.permission_gate: p.error('--pg-receiver requires --permission-gate')
if a.permission_gate and not a.clamp_cause: p.error('--permission-gate requires --clamp-cause')
if a.clamp_cause and not a.en_clamp: p.error('--clamp-cause requires --en-clamp')
if a.en_clamp and not a.en_driver: p.error('--en-clamp requires --en-driver')
if a.en_driver and not a.supervisor: p.error('--en-driver requires --supervisor')
a.out.mkdir(parents=True,exist_ok=False)
files=['manual_button_candidate.json','manual_release_gate_candidate.json','manual_release_mr_buffer_candidate.json','manual_release_timer_candidate.json','manual_rearm_latch_candidate.json']
if a.supervisor: files.append('manual_rearm_supervisor_candidate.json')
if a.en_driver: files.append('main_enable_driver_candidate.json')
if a.en_clamp: files.append('main_enable_clamp_candidate.json')
if a.clamp_cause: files.append('main_clamp_cause_candidate.json')
if a.pg_receiver: files.append('pg_receiver_candidate.json')
data={f:json.loads((ROOT/'schematics/power'/f).read_text()) for f in files}
parts=[]
def add(ref,part,nets,source=None):
 parts.append({'reference':ref,'part':part,'pins':{str(i):n for i,n in enumerate(nets,1)},'source':source})
add('U1',data[files[0]]['part_number'],['GND','BUTTON_RAW','BUTTON_RELEASED','LOGIC3V3'],files[0])
add('U2','SN74LVC1G04DBVR',[None,'BUTTON_RELEASED','GND','PRESS','LOGIC3V3'],files[0])
add('U3',data[files[1]]['part_number'],['RESET_N','RAW_RELEASED_CONDITIONED','GND','GND','GND',None,'GND',None,'GND','GND','GND','RELEASE_CONDITION','BUTTON_RELEASED','LOGIC3V3'],files[1])
add('U4',data[files[2]]['part_number'],[None,'RELEASE_CONDITION','GND','RELEASE_MR','LOGIC3V3'],files[2])
add('U5',data[files[3]]['part_number'],['RELEASE_QUALIFIED','GND','RELEASE_MR','TIMER_CT','LOGIC3V3','LOGIC3V3'],files[3])
add('U6',data[files[4]]['part_number'],['RESET_N','LOGIC3V3','RELEASE_QUALIFIED','LOGIC3V3','ARMED',None,'GND',None,'ENABLE_PERMISSION','LOGIC3V3','PRESS','ARMED','RESET_N','LOGIC3V3'],files[4])
add('R1','100k value candidate; exact part/tolerance pending',['LOGIC3V3','TIMER_CT'])
add('R2','100k value candidate; exact part/tolerance pending',['LOGIC3V3','RELEASE_QUALIFIED'])
for i in range(1,7):add(f'C{i}','100nF local ceramic candidate; exact part pending',['LOGIC3V3','GND'])
add('SW1','NO momentary enable button; part/contact characteristics pending',['BUTTON_RAW','GND'])
if a.supervisor:
 add('U7',data['manual_rearm_supervisor_candidate.json']['part_number'],['RESET_N','GND','LOGIC3V3','SUPERVISOR_CT','LOGIC3V3','LOGIC3V3'],'manual_rearm_supervisor_candidate.json')
 add('R3','100k value candidate; exact part/tolerance pending',['LOGIC3V3','SUPERVISOR_CT'])
 add('R4','100k value candidate; exact part/tolerance pending',['LOGIC3V3','RESET_N'])
 add('C7','100nF local ceramic candidate; exact part pending',['LOGIC3V3','GND'])
if a.en_driver:
 add('U8',data['main_enable_driver_candidate.json']['part_number'],[None,'POWER_ENABLE_COMMAND','GND','MAIN_EFUSE_EN','LOGIC3V3'],'main_enable_driver_candidate.json')
 add('R5','39k pulldown; total +/-1% budget, part pending',['MAIN_EFUSE_EN','GND'])
 add('R6','220k pulldown; total +/-1% budget, part pending',['POWER_ENABLE_COMMAND','GND'])
 add('C8','100nF local ceramic candidate; part pending',['LOGIC3V3','GND'])
if a.en_clamp:
 next(x for x in parts if x['reference']=='U8')['pins']['4']='ENABLE_BUFFER_OUT'
 add('R7','4.7k series; total +/-1% budget, part pending',['ENABLE_BUFFER_OUT','MAIN_EFUSE_EN'])
 add('U9',data['main_enable_clamp_candidate.json']['part_number'],['MAIN_EFUSE_EN','GND','EFUSE_INPUT_5V','CLAMP_CT','LOGIC3V3','EFUSE_INPUT_5V'],'main_enable_clamp_candidate.json')
 add('R8','100k CT candidate; part pending',['EFUSE_INPUT_5V','CLAMP_CT'])
 add('C9','100nF local ceramic candidate; part pending',['EFUSE_INPUT_5V','GND'])
if a.clamp_cause:
 next(x for x in parts if x['reference']=='U9')['pins']['1']='RAIL_HEALTH_N'
 next(x for x in parts if x['reference']=='U7')['pins']['3']='RAIL_HEALTH_N'
 add('U10',data['main_clamp_cause_candidate.json']['part_number'],['MAIN_EFUSE_EN','GND','CLAMP_MR_5V',None,'EFUSE_INPUT_5V','EFUSE_INPUT_5V'],'main_clamp_cause_candidate.json')
 add('U11',data['main_clamp_cause_candidate.json']['level_buffer_part'],[None,'RAIL_HEALTH_N','GND','CLAMP_MR_5V','EFUSE_INPUT_5V'],'main_clamp_cause_candidate.json')
 add('R9','10k cause pullup; total +/-1% budget, part pending',['LOGIC3V3','RAIL_HEALTH_N'])
 for n in [10,11]: add(f'C{n}','100nF local ceramic candidate; part pending',['EFUSE_INPUT_5V','GND'])
if a.permission_gate:
 gate=next(x for x in parts if x['reference']=='U3')['pins']
 gate.update({'3':'ENABLE_PERMISSION','4':'SEQUENCE_ENABLE_REQUEST','5':'RESET_N','6':'POWER_ENABLE_COMMAND'})
if a.pg_receiver:
 pg=data['pg_receiver_candidate.json']
 add('U12',pg['part'],[pg['pins'][str(i)] if pg['pins'][str(i)]!='NC' else None for i in range(1,7)],'pg_receiver_candidate.json')
 add('U13',pg['buffer']['part'],[pg['buffer']['pins'][str(i)] for i in range(1,6)],'pg_receiver_candidate.json')
 for ref,passive in zip(['R10','R11','R12','R13','C12'],pg['passives']):
  value=str(passive.get('value_ohm',passive.get('value_F')))
  add(ref,value+' value candidate; exact part pending',[passive['from'],passive['to']])
 add('C13','100nF local ceramic candidate; exact part pending',['LOGIC3V3','GND'])
ports={'LOGIC3V3':'upstream logic rail; power budget and independent supervision unfinished','GND':'common reference; physical return routing unfinished','RESET_N':'independent health-qualified clear input; low on stop/fault/invalid power; must not depend on button debounce/timer','RAW_RELEASED_CONDITIONED':'unfinished protected raw-input interface from BUTTON_RAW; not a direct wire','ENABLE_PERMISSION':'logic output only; physical default-off power stage unfinished'}
if a.supervisor: ports['RESET_N']='U7 open-drain rail reset plus external stop/fault sinks; sink components, fanout and fail-state behavior unfinished; never push-pull drive'
if a.en_driver:
 ports['POWER_ENABLE_COMMAND']='output of unfinished startup/stop sequencer, not a wire from ENABLE_PERMISSION'
 ports['MAIN_EFUSE_EN']='TPS259823 pin6; conditional driver, brownout/default-off qualification incomplete'
if a.en_clamp: ports['EFUSE_INPUT_5V']='input side of eFuse; must remain within supervisor supply rating, never raw battery'
if a.permission_gate:
 ports.pop('POWER_ENABLE_COMMAND')
 ports['SEQUENCE_ENABLE_REQUEST']='unfinished startup/PG sequencer output; hardware gate also requires retained permission and RESET_N'
if a.pg_receiver:
 ports['MAIN_EFUSE_PG']='TPS259823 pin13; conditional analog receiver, open-wire fault coverage unfinished'
 ports['PG_CONDITIONED']='U13 pin4 output to unfinished startup sequencer; invalid during power transitions'
report={'scope':__doc__,'parts':parts,'interfaces':ports,'source_sha256':{f:hashlib.sha256((ROOT/'schematics/power'/f).read_bytes()).hexdigest() for f in files},'part_count':len(parts),'pin_count':sum(len(x['pins']) for x in parts),'logical_composition_only':True,'electrical_qualification':False,'manufacturing_release':False}
report['assembly_overrides'] = ['U8 pin4 routed through R7 to MAIN_EFUSE_EN; overrides direct output in individual driver candidate'] if a.en_clamp else []
if a.clamp_cause: report['assembly_overrides'] += ['U9 RESET goes to RAIL_HEALTH_N instead of EN; U7 MR receives RAIL_HEALTH_N instead of LOGIC3V3; U11 level buffer and U10 reset follower drive EN']
if a.permission_gate: report['assembly_overrides'] += ['U3 unused second AND gate: pins3,4,5 accept ENABLE_PERMISSION, SEQUENCE_ENABLE_REQUEST, RESET_N; pin6 drives U8 input POWER_ENABLE_COMMAND']
# Wiring invariants that prevent accidental inversion or delayed stop substitution.
refs={x['reference']:x for x in parts}
assert refs['U6']['pins']['1']==refs['U6']['pins']['13']=='RESET_N'
assert refs['U5']['pins']['1']==refs['U6']['pins']['3']=='RELEASE_QUALIFIED'
assert refs['U4']['pins']['4']==refs['U5']['pins']['3']=='RELEASE_MR'
assert refs['U6']['pins']['11']==refs['U2']['pins']['4']=='PRESS'
assert refs['U3']['pins']['2']!=refs['U1']['pins']['2']
if a.en_driver:
 assert refs['U8']['pins']['2'] != refs['U6']['pins']['9']
 if a.en_clamp:
  assert refs['U8']['pins']['4'] == refs['R7']['pins']['1'] == 'ENABLE_BUFFER_OUT'
  clamp_ref = 'U10' if a.clamp_cause else 'U9'
  assert refs[clamp_ref]['pins']['1'] == refs['R7']['pins']['2'] == refs['R5']['pins']['1'] == 'MAIN_EFUSE_EN'
  if a.clamp_cause:
   assert refs['U9']['pins']['1'] == refs['U7']['pins']['3'] == refs['U11']['pins']['2'] == 'RAIL_HEALTH_N'
   assert refs['U11']['pins']['4'] == refs['U10']['pins']['3'] == 'CLAMP_MR_5V'
  assert refs['U9']['pins']['1'] != refs['U7']['pins']['1']
 else: assert refs['U8']['pins']['4'] == refs['R5']['pins']['1'] == 'MAIN_EFUSE_EN'
if a.permission_gate:
 assert refs['U3']['pins']['3']==refs['U6']['pins']['9']=='ENABLE_PERMISSION'
 assert refs['U3']['pins']['5']==refs['U6']['pins']['13']=='RESET_N'
 assert refs['U3']['pins']['6']==refs['U8']['pins']['2']=='POWER_ENABLE_COMMAND'
if a.pg_receiver:
 assert refs['U12']['pins']['1']==refs['U13']['pins']['2']==refs['R13']['pins']['2']=='PG_CONDITIONED_OD'
 assert refs['U12']['pins']['3']==refs['R11']['pins']['2']==refs['R12']['pins']['1']=='PG_DIVIDED'
 assert refs['U12']['pins']['5']==refs['U13']['pins']['5']=='LOGIC3V3'
 assert all(net!='RESET_N' for ref in ['U12','U13'] for net in refs[ref]['pins'].values())
(a.out/'assembly.json').write_text(json.dumps(report,indent=2)+'\n')
with (a.out/'connections.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['reference','part','pin','net'])
 for x in parts:
  for pin,net in x['pins'].items():w.writerow([x['reference'],x['part'],pin,net or 'NC'])
print(json.dumps({k:report[k] for k in ['part_count','pin_count','electrical_qualification','manufacturing_release']}))
