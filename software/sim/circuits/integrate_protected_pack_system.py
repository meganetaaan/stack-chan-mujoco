"""Explicit protected-pack topology candidate; connectivity is not qualification."""
import copy,csv,hashlib,json
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'schematics/power/protected_pack_system_candidate_v1';OUT.mkdir(exist_ok=True)
files=[ROOT/'schematics/power/system_power_integration_candidate_v1/assembly.json',ROOT/'schematics/power/pack_control_ramp_candidate_v1/assembly.json',ROOT/'schematics/power/pack_main_allow_interface_candidate_v1/assembly.json']
old,control,interface=[json.loads(f.read_text()) for f in files]
remove={p['reference'] for p in old['parts'] if p['reference'].startswith('BAT__')}|{'SYS__U_AUX_START_ISO','SYS__C_AUX_ISO_PRIMARY','SYS__C_AUX_ISO_SECONDARY'}
assert len(remove)==103 and len(old['parts'])==250
# This is a deliberate topology choice, not silent name normalization.
bindings={'CELL_POS_UNFUSED':'PACK_OUTPUT_POS','CELL_B_MINUS':'PACK_RETURN','CELL_POS_FUSED_RAW':'PACK_FUSED_RAW','CELL_POS_FUSED':'PACK_FUSED_REVERSE_PROTECTED','PACK_POS_PROTECTED':'PACK_FUSED_REVERSE_PROTECTED'}
parts=[]
for group,data in [('retained',old),('pack_control',control),('main_interface',interface)]:
 for item in data['parts']:
  if group=='retained' and item['reference'] in remove:continue
  p=copy.deepcopy(item);p['integration_group']=group;p['pins']={pin:bindings.get(net,net) for pin,net in p['pins'].items()};parts.append(p)
assert len(parts)==191 and len({p['reference'] for p in parts})==191
refs={p['reference']:p for p in parts};nets=defaultdict(list)
for p in parts:
 for pin,net in p['pins'].items():
  if net:nets[net].append({'reference':p['reference'],'pin':pin})
assert not any(n.startswith(('CELL_','BQ_')) for n in nets)
assert refs['INLET__J_PACK']['pins']=={'+':'PACK_OUTPUT_POS','-':'PACK_RETURN'}
assert refs['U_CTRL_INPUT_LIMIT']['pins']['8']==refs['SYS__U_LOGIC_PROTECT']['pins']['8']==refs['TAB5__U_PROTECT']['pins']['8']=='PACK_FUSED_REVERSE_PROTECTED'
assert refs['IF_MAIN__U_BUFFER']['pins']['2']==refs['CTRL__U_MAIN_GATE']['pins']['4']=='MAIN_START_ALLOW'
assert refs['IF_MAIN__U_BUFFER']['pins']['4']==refs['SYS__U3']['pins']['4']=='SYS__SEQUENCE_ENABLE_REQUEST'
assert refs['SYS__U3']['pins']['3']=='SYS__ENABLE_PERMISSION' and refs['SYS__U3']['pins']['5']=='SYS__RESET_N'
# The auxiliary output is intentionally NOT connected before checking its domain crossing.
assert 'LOGIC_START_ALLOW' in nets and 'SYS__LOGIC_START_ALLOW' in nets
open_ports=['LOGIC_START_ALLOW','SYS__LOGIC_START_ALLOW','TAB5_START_ALLOW','PACK_UV_WARN_N','SYS__LEFT_REGULATOR_ALLOW','SYS__RIGHT_REGULATOR_ALLOW','SYS__SEQUENCE_CLEAR_REQUEST']
r={'status':'unified_protected_pack_topology_candidate_not_operational','parts':parts,'external_battery':{'candidate':'ROBOTIS LB-020','terminals':['PACK_OUTPUT_POS','PACK_RETURN'],'not_in_reference_count':True,'PCM_limits_unverified':True},'removed_references':sorted(remove),'explicit_power_bindings':bindings,'interconnects':copy.deepcopy(old['interconnects']),'unresolved_signal_ports':{n:nets.get(n,[]) for n in open_ports},'checks':{'unique191references':True,'no_raw_cell_BQ_nets':True,'common_protected_pack_return':True,'main_permission_keeps_reset_and_manual_AND_inputs':True,'aux_crossing_not_silently_joined':True},'architecture_decisions':['Use external pack PCM for cell protection; old raw-cell BQ/shunt removed','Robot main fuse and reverse input remain before distribution','Control/logic/Tab5/servo branches share reverse-protected bus; old BQ master disconnect is absent','Drive shutdown is assigned to branch enable/stop paths, not whole-pack disconnection; this allocation remains unqualified'],'remaining':['Pack PCM ratings/reverse-current/recovery and fuse coordination','Loss of master disconnect: standby drain and all-branch fault-energy limits','Aux logic crossing and Tab5/UV/manual input interfaces','Both regulator allow drivers and reset sequencing','12 unselected legacy references and pending-value parts','Whole load/inrush/regeneration/short/temperature/tolerance verification','Board/harness mechanics and full mass allocation'],'electrically_operational':False,'manufacturing_release':False,'source_sha256':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}}
(OUT/'assembly.json').write_text(json.dumps(r,indent=2)+'\n')
with (OUT/'bom.csv').open('w',newline='') as f:
 w=csv.writer(f,lineterminator='\n');w.writerow(['reference','part','group']);w.writerows([p['reference'],p.get('part'),p['integration_group']] for p in parts)
with (OUT/'connections.csv').open('w',newline='') as f:
 w=csv.writer(f,lineterminator='\n');w.writerow(['reference','pin','net']);w.writerows([p['reference'],pin,net] for p in parts for pin,net in p['pins'].items())
print(json.dumps({'references':len(parts),'removed':len(remove),'unresolved_ports':open_ports,'operational':False}))
