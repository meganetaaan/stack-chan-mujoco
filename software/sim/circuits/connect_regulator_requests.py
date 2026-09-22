"""Independent pre-eFuse regulator startup requests, gated by CTRL permit latch."""
import copy,csv,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
src=ROOT/'schematics/power/protected_pack_system_candidate_v5/assembly.json'
out=ROOT/'schematics/power/protected_pack_system_candidate_v6'
val=ROOT/'validation/regulator_request_connection_v1'
for d in (out,val):d.mkdir(exist_ok=True)
a=json.loads(src.read_text());r=copy.deepcopy(a);parts={p['reference']:p for p in r['parts']}
assert len(parts)==194
assert parts['SYS__R9']['pins']=={'1':'SYS__LOGIC3V3','2':'SYS__RAIL_HEALTH_N'}
parts['SYS__R9'].update(part='TNPW060310K0BEEA',value_ohm=10000,total_tolerance_budget=0.01,selection_basis='Reuse selected10k part;1% is engineering total budget, not initial tolerance')
host=parts['CTRL__U_HOST']; assert host['part']=='STM32G030F6P6'
assert parts['CTRL__U_PERMIT_LATCH']['pins']['5']=='CTRL_LATCH_PERMIT'
for side,pin in [('LEFT','12'),('RIGHT','13')]:
 assert host['pins'][pin] is None
 raw=f'CTRL_{side}_REG_REQUEST_RAW';conditioned=f'CTRL_{side}_REG_REQUEST';allow=f'SYS__{side}_REGULATOR_ALLOW';prefix=f'IF_REG_{side}__'
 host['pins'][pin]=raw
 assert parts[f'SYS__{side}_R_REG_EN_SER']['pins']['1']==allow
 r['parts'] += [
  {'reference':prefix+'U_SCHMITT','part':'74LVC1G17GV','pins':{'1':None,'2':raw,'3':'PACK_RETURN','4':conditioned,'5':'CTRL3V3'},'integration_group':'regulator_request'},
  {'reference':prefix+'U_AND','part':'SN74LVC1G08DBVR','pins':{'1':conditioned,'2':'CTRL_LATCH_PERMIT','3':'PACK_RETURN','4':allow,'5':'CTRL3V3'},'integration_group':'regulator_request'},
  {'reference':prefix+'R_PD','part':'TNPW060310K0BEEA','value_ohm':10000,'pins':{'1':raw,'2':'PACK_RETURN'},'placement':'At Schmitt input','integration_group':'regulator_request'},
 ]
 for name in ('C_SCHMITT','C_AND'):
  r['parts'].append({'reference':prefix+name,'part':'GRM31C5C1H104JA01L','value_F':1e-7,'pins':{'1':'CTRL3V3','2':'PACK_RETURN'},'integration_group':'regulator_request'})
 r['unresolved_signal_ports'].pop(allow)
assert len(r['parts'])==len({p['reference'] for p in r['parts']})==204
changed=[p['reference'] for p in a['parts'] if p['pins']!=parts[p['reference']]['pins']]
assert changed==['CTRL__U_HOST']
# Nominal network: ENA and ENB both pull up to VIN. Thresholds are not assumed.
rint=1/(1/1e6+1/(1e6+1e4));rs=100.;pd=2210.;vin=12.6
rows=[]
for voltage in (0.,.4,2.4,3.3,3.6):
 ena=(vin/rint+voltage/rs)/(1/rint+1/rs+1/pd)
 rows.append({'driver_V':voltage,'ENA_nominal_V':ena,'driver_nominal_A':(voltage-ena)/rs})
report={'source_sha256':{str(src.relative_to(ROOT)):hashlib.sha256(src.read_bytes()).hexdigest()},
 'MCU_assignments':{'12':'PA5 left request','13':'PA6 right request'},'old_pin_maps_changed':changed,'existing_part_selection':{'SYS__R9':'TNPW060310K0BEEA'},
 'normal_valid_supply_truth_table':[{'request':q,'CTRL_latch_permit':p,'regulator_allow':q and p} for q in (False,True) for p in (False,True)],
 'SYS_reset_is_not_an_input':True,
 'nominal_module_network':{'VIN_V':vin,'ENA_to_VIN_ohm':1e6,'ENB_to_VIN_ohm':1e6,'ENA_ENB_ohm':1e4,'external_series_ohm':rs,'external_pulldown_ohm':pd,'rows':rows,'driver_high_impedance_ENA_V':vin*pd/(pd+rint)},
 'new_CTRL_nominal_capacitance_F':4e-7,
 'new_CTRL_resistive_allocation_A':2*(3.6/(10000*.99)+3.6/((100+2210)*.99)),
 'resistive_allocation_scope':'3.6V, external resistor1% engineering envelope; not complete added current. Module injection not counted as CTRL supply load.',
 'sources':[{'url':'https://www.st.com/resource/en/datasheet/stm32g030f6.pdf','revision':'DS12991 Rev6','section':'Table12 TSSOP20 pins12/13'},
 {'url':'https://www.ti.com/lit/ds/symlink/sn74lvc1g08.pdf','revision':'AA August2026','sections':['4 DBV pinout','5.3 input speed','5.5 VOH/VOL/Ioff']},
 {'url':'https://assets.nexperia.com/documents/data-sheet/74LVC1G17.pdf','revision':'16.1 September2024','sections':['2 unlimited input edge','6 GV pinout']},
 {'url':'https://www.pololu.com/product/5671','section':'Connections ENA and ENB'}],
 'remaining':['Module ENA guaranteed low/high thresholds and internal resistor tolerance not specified by product page',
 'Unpowered module driven high and CTRL loss with VIN alive: injection/partial rail behavior',
 'GPIO reset state/leakage, Schmitt output and permit fanout edge/DC margins',
 'Brownout latch clearing and no automatic restart across all rail orders',
 'Update complete CTRL budget:4ICs,2GPIO loads,2ENA loads,400nF plus dynamic/leakage',
 'Firmware sequencing contract and manual-input authorization not implemented'],
 'firmware_contract':['Default both requests low','CTRL supervisor/watchdog valid and explicit arm before permit latch set','Start regulators independently of SYS reset, qualify source voltages, then allow existing manual servo rearm','Any CTRL fault clears permit; do not automatically rearm on power restoration'],
 'qualified':False,'manufacturing_release':False}
r['regulator_request_interface']=report;r['source_sha256']=report['source_sha256'];r['status']='regulator_requests_connected_not_operational'
r['checks'].pop('unique194references',None);r['checks']['unique204references']=True
r['remaining'].append('Regulator request electrical qualification, partial-power behavior and load budget')
(out/'assembly.json').write_text(json.dumps(r,indent=2)+'\n');(val/'report.json').write_text(json.dumps(report,indent=2)+'\n')
for name,header,rows in [('bom.csv',['reference','part','group'],[[x['reference'],x.get('part'),x.get('integration_group')] for x in r['parts']]),('connections.csv',['reference','pin','net'],[[x['reference'],pin,net] for x in r['parts'] for pin,net in x['pins'].items()])]:
 with (out/name).open('w',newline='') as f:
  w=csv.writer(f,lineterminator='\n');w.writerow(header);w.writerows(rows)
print(json.dumps({'references':204,'remaining_ports':list(r['unresolved_signal_ports']),'added_resistive_allocation_A':report['new_CTRL_resistive_allocation_A'],'qualified':False}))
