"""Connect the Tab5 branch request to the protected-pack candidate, not firmware."""
import copy
import csv
import hashlib
import itertools
import json
from pathlib import Path
from tab5_restart_model import Inputs, State, outputs

ROOT=Path(__file__).resolve().parents[3]
SRC=ROOT/'schematics/power/protected_pack_system_candidate_v6/assembly.json'
OUT=ROOT/'schematics/power/protected_pack_system_candidate_v7'
VAL=ROOT/'validation/tab5_request_connection_v1'
for path in (OUT,VAL):path.mkdir(exist_ok=True)
a=json.loads(SRC.read_text());r=copy.deepcopy(a)
p={x['reference']:x for x in r['parts']}
assert len(p)==204
assert p['CTRL__U_HOST']['part']=='STM32G030F6P6' and p['CTRL__U_HOST']['pins']['14'] is None
assert p['TAB5__U_PROTECT']['part']=='TPS26601RHFR'
assert p['TAB5__U_PROTECT']['pins']['14']=='TAB5_SHDN'
assert p['TAB5__U_PROTECT']['pins']['17']=='PACK_RETURN'
assert p['TAB5__U_PROTECT']['pins']['15']=='TAB5_PROTECT_RTN'
assert p['TAB5__R_SHDN_SER']['part']=='TNPW06031K00BEEA'
assert p['TAB5__R_SHDN_SER']['pins']=={'1':'TAB5_START_ALLOW','2':'TAB5_SHDN'}
assert p['TAB5__R_SHDN_PD']['part']=='TNPW060310K0BEEA'
assert p['TAB5__R_SHDN_PD']['pins']=={'1':'TAB5_SHDN','2':'PACK_RETURN'}
selection_path=ROOT/'schematics/power/tab5_startup_parameter_candidate_v1/selection.json'
selection=json.loads(selection_path.read_text())
assert selection['source_sha256'][str(SRC.relative_to(ROOT))]==hashlib.sha256(SRC.read_bytes()).hexdigest()
selected=selection['selected_part']
assert selected['reference']=='TAB5__C_DVDT'
p['TAB5__C_DVDT'].update(part=selected['part'],value_F=selected['value_F'],selection_basis='tab5_startup_parameter_candidate_v1; nominal ramp candidate, startup not qualified')
p['CTRL__U_HOST']['pins']['14']='CTRL_TAB5_REQUEST_RAW'
new=[
 {'reference':'IF_TAB5__U_SCHMITT','part':'74LVC1G17GV','pins':{'1':None,'2':'CTRL_TAB5_REQUEST_RAW','3':'PACK_RETURN','4':'CTRL_TAB5_REQUEST','5':'CTRL3V3'}},
 {'reference':'IF_TAB5__U_AND','part':'SN74LVC1G08DBVR','pins':{'1':'CTRL_TAB5_REQUEST','2':'CTRL_LATCH_PERMIT','3':'PACK_RETURN','4':'TAB5_START_ALLOW','5':'CTRL3V3'}},
 {'reference':'IF_TAB5__R_PD','part':'TNPW060310K0BEEA','value_ohm':10000,'pins':{'1':'CTRL_TAB5_REQUEST_RAW','2':'PACK_RETURN'}},
]
for suffix in ['SCHMITT','AND']:
 new.append({'reference':'IF_TAB5__C_'+suffix,'part':'GRM31C5C1H104JA01L','value_F':1e-7,'pins':{'1':'CTRL3V3','2':'PACK_RETURN'}})
for part in new:part['integration_group']='tab5_request'
r['parts']+=new
assert r['unresolved_signal_ports']['TAB5_START_ALLOW']==[{'reference':'TAB5__R_SHDN_SER','pin':'1'}]
r['unresolved_signal_ports'].pop('TAB5_START_ALLOW')
assert set(r['unresolved_signal_ports'])=={'PACK_UV_WARN_N'}
assert len(r['parts'])==len({x['reference'] for x in r['parts']})==209
changed=[x['reference'] for x in a['parts'] if x!=p[x['reference']]]
assert changed==['TAB5__C_DVDT','CTRL__U_HOST']
# Transfer the existing static comparison only after checking exact receiver/resistor choices.
aux_path=ROOT/'validation/aux_start_connection_v1/report.json'
aux=json.loads(aux_path.read_text())
assert all(aux['checks'].values())
truth=[]
for request,permit in itertools.product([False,True],repeat=2):
 truth.append({'request':request,'CTRL_latch_permit':permit,'tab5_allow':request and permit})
# Design-contract composition: model outputs -> request -> hardware AND.
# Enumerate relevant state/input combinations; these are NOT transistor simulations.
contract=[]
for phase in ['OFF','BOOT','READY','RUN','SHUTDOWN']:
 for healthy,continuous,valid,ready,stop,ack,permit in itertools.product([False,True],repeat=7):
  i=Inputs(healthy=healthy,continuous_observation=continuous,power_valid=valid,ready=ready,stop=stop,shutdown_ack=ack)
  desired=outputs(State(phase=phase),i)
  actual=desired.tab5_allow and permit
  drive=desired.drive_permission and permit
  assert not actual or (permit and healthy and continuous)
  assert not drive or (actual and valid and ready and not stop)
  contract.append({'phase':phase,'healthy':healthy,'continuous':continuous,'power_valid':valid,'ready':ready,
                   'stop':stop,'shutdown_ack':ack,'permit':permit,'tab5_allow':actual,'drive_permission':drive})
assert len(contract)==640
with (VAL/'contract_combinations.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(contract[0]),lineterminator='\n');w.writeheader();w.writerows(contract)
report={
 'source_sha256':{str(x.relative_to(ROOT)):hashlib.sha256(x.read_bytes()).hexdigest() for x in [SRC,aux_path,selection_path,Path(__file__).with_name('tab5_restart_model.py')]},
 'MCU_assignment':{'package':'TSSOP20','pin':14,'port':'PA7','net':'CTRL_TAB5_REQUEST_RAW'},
 'normal_supply_truth_table':truth,'contract_combination_count':640,
 'static_receiver_comparison':aux['calculations'],
 'comparison_scope':'Same TPS26601 and 1k series/10k pulldown; inherits aux assumptions, no new analog qualification',
 'added_CTRL_resistive_allocation_A':3.6/(10000*.99)+aux['calculations']['CTRL_high_extra_branch_current_A_at3_6V'],
 'added_CTRL_capacitance_F':2e-7,
 'ground_offset_comparison':{
  'placement':'SHDN pulldown return at receiver GND pin17, separate from RTN pin15',
  'low_node_margin_V':.4-aux['calculations']['low_SHDN_V_at_driver3V_table_bound'],
  'driver_ground_positive_limit_V':(.4-aux['calculations']['low_SHDN_V_at_driver3V_table_bound'])*(1+990/10100),
  'scope':'DC point comparison with transferred10uA leakage allocation; no production routing allowance or transient bound'},
 'extra_current_not_included':['Two new IC supply currents','Input leakage and switching current','GPIO and permit-output dynamic load'],
 'old_parts_changed':changed,'old_protection_part_values_changed':['TAB5__C_DVDT'],
 'Tab5_ramp_selection':selected,
 'implementation_contract':[
  'PA7 low by default; configure output data low before enabling output mode',
  'Drive PA7 from Tab5 restart contract tab5_allow, not from raw user start button',
  'Normal stop first removes drive permission, keeps Tab5 on until fresh shutdown acknowledgement',
  'CTRL watchdog/supervisor clears hardware permit even during graceful shutdown',
  'Fresh verified off interval and new start request required after restart; do not restore old request',
  'SYS_RESET_N is not a Tab5 startup prerequisite; keep independent servo protection and manual rearm',
 ],
 'remaining':[
  'off_verified, power_valid, ready and shutdown_ack detection/communication not wired or implemented',
  'Tab5 current limit selection; selected100nF DVDT startup/thermal qualification, input capacitance/inrush and connector wiring',
  'GPIO reset/leakage, Schmitt-to-AND edge timing and permit fanout',
  'Full CTRL budget, intermediate-supply behavior and actual shutdown timing',
  'SHDN leakage allocation at other voltages/3S input range, eFuse recovery/backfeed',
  'All-rail startup, faults, load/temperature and PCB/harness verification',
 ],
 'firmware_implemented':False,'electrically_operational':False,'manufacturing_release':False,
 'sources':[
  {'url':'https://www.st.com/resource/en/datasheet/stm32g030f6.pdf','revision':'DS12991 Rev6','section':'Table12 PA7 TSSOP20 pin14'},
  {'url':'https://www.ti.com/lit/ds/symlink/tps2660.pdf','basis':'Existing aux_start_connection_v1 reviewed RevG static comparison'},
  {'url':'https://www.ti.com/lit/ds/symlink/sn74lvc1g08.pdf','revision':'AA','section':'Pinout, VOH/VOL and Ioff'},
  {'url':'https://assets.nexperia.com/documents/data-sheet/74LVC1G17.pdf','basis':'Existing selected GV Schmitt input buffer'},
 ],
}
r['tab5_request_interface']=report
r['status']='tab5_request_connected_not_operational'
r['source_sha256']=report['source_sha256']
r['checks'].pop('unique204references',None);r['checks']['unique209references']=True
r['remaining'].append('Tab5 request/detector protocol, electrical margins and whole load budget remain')
(OUT/'assembly.json').write_text(json.dumps(r,indent=2)+'\n')
(VAL/'report.json').write_text(json.dumps(report,indent=2)+'\n')
for name,header,rows in [
 ('bom.csv',['reference','part','group'],[[x['reference'],x.get('part'),x.get('integration_group')] for x in r['parts']]),
 ('connections.csv',['reference','pin','net'],[[x['reference'],pin,net] for x in r['parts'] for pin,net in x['pins'].items()])]:
 with (OUT/name).open('w',newline='') as f:
  w=csv.writer(f,lineterminator='\n');w.writerow(header);w.writerows(rows)
print(json.dumps({'parts':209,'changed_existing':changed,'remaining_ports':list(r['unresolved_signal_ports']),
 'contract_combinations':len(contract),'added_resistive_A':report['added_CTRL_resistive_allocation_A']}))
