"""Package the current manual-rearm candidate and explicit unfinished interfaces."""
import argparse,csv,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--supervisor',action='store_true');p.add_argument('--en-driver',action='store_true');p.add_argument('--en-clamp',action='store_true');a=p.parse_args();
if a.en_clamp and not a.en_driver: p.error('--en-clamp requires --en-driver')
if a.en_driver and not a.supervisor: p.error('--en-driver requires --supervisor')
a.out.mkdir(parents=True,exist_ok=False)
files=['manual_button_candidate.json','manual_release_gate_candidate.json','manual_release_mr_buffer_candidate.json','manual_release_timer_candidate.json','manual_rearm_latch_candidate.json']
if a.supervisor: files.append('manual_rearm_supervisor_candidate.json')
if a.en_driver: files.append('main_enable_driver_candidate.json')
if a.en_clamp: files.append('main_enable_clamp_candidate.json')
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
ports={'LOGIC3V3':'upstream logic rail; power budget and independent supervision unfinished','GND':'common reference; physical return routing unfinished','RESET_N':'independent health-qualified clear input; low on stop/fault/invalid power; must not depend on button debounce/timer','RAW_RELEASED_CONDITIONED':'unfinished protected raw-input interface from BUTTON_RAW; not a direct wire','ENABLE_PERMISSION':'logic output only; physical default-off power stage unfinished'}
if a.supervisor: ports['RESET_N']='U7 open-drain rail reset plus external stop/fault sinks; sink components, fanout and fail-state behavior unfinished; never push-pull drive'
if a.en_driver:
 ports['POWER_ENABLE_COMMAND']='output of unfinished startup/stop sequencer, not a wire from ENABLE_PERMISSION'
 ports['MAIN_EFUSE_EN']='TPS259823 pin6; conditional driver, brownout/default-off qualification incomplete'
if a.en_clamp: ports['EFUSE_INPUT_5V']='input side of eFuse; must remain within supervisor supply rating, never raw battery'
report={'scope':__doc__,'parts':parts,'interfaces':ports,'source_sha256':{f:hashlib.sha256((ROOT/'schematics/power'/f).read_bytes()).hexdigest() for f in files},'part_count':len(parts),'pin_count':sum(len(x['pins']) for x in parts),'logical_composition_only':True,'electrical_qualification':False,'manufacturing_release':False}
report['assembly_overrides'] = ['U8 pin4 routed through R7 to MAIN_EFUSE_EN; overrides direct output in individual driver candidate'] if a.en_clamp else []
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
  assert refs['U9']['pins']['1'] == refs['R7']['pins']['2'] == refs['R5']['pins']['1'] == 'MAIN_EFUSE_EN'
  assert refs['U9']['pins']['1'] != refs['U7']['pins']['1']
 else: assert refs['U8']['pins']['4'] == refs['R5']['pins']['1'] == 'MAIN_EFUSE_EN'
(a.out/'assembly.json').write_text(json.dumps(report,indent=2)+'\n')
with (a.out/'connections.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['reference','part','pin','net'])
 for x in parts:
  for pin,net in x['pins'].items():w.writerow([x['reference'],x['part'],pin,net or 'NC'])
print(json.dumps({k:report[k] for k in ['part_count','pin_count','electrical_qualification','manufacturing_release']}))
