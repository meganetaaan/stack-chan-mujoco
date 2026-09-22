"""Concrete standalone controller candidate; external interfaces remain unqualified."""
import copy,csv,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'schematics/power/pack_start_controller_candidate_v1'
OUT.mkdir(exist_ok=True)
source=ROOT/'schematics/power/system_power_integration_candidate_v1/assembly.json'
a=json.loads(source.read_text());byref={p['reference']:p for p in a['parts']}
tokens=['BQ_HOST','BQ_WD','BQ_RESET','BQ_PERMIT','BQ_MAIN','BQ_AUX','REQUEST_RAW','ARM_EDGE']
selected=[p for p in a['parts'] if p['reference'].startswith('BAT__') and any(t in p['reference'] for t in tokens)]
assert len(selected)==25
rename={'CELL_B_MINUS':'PACK_RETURN','BQ_CTRL3V3':'CTRL3V3',
        'BQ_AUX_START_REQUEST':'LOGIC_START_ALLOW','BQ_ALLOW_BMINUS':'MAIN_START_ALLOW',
        'BQ_ALERT_N':'PACK_UV_WARN_N'}
def net(n):
    if n is None:return None
    return rename.get(n,n.replace('BQ_','CTRL_'))
parts=[]
for original in selected:
    p=copy.deepcopy(original)
    p['reference']=p['reference'].replace('BAT__','CTRL__').replace('BQ_','')
    p['pins']={pin:net(n) for pin,n in p['pins'].items()}
    p['source_reference']=original['reference'];p['source_assembly']=str(source.relative_to(ROOT))
    if p['reference']=='CTRL__U_HOST':
        p['pins']['1']=None;p['pins']['20']=None
        p['role']='Pack-side startup coordination; requires new firmware and manual-input interface'
    parts.append(p)
for old,new,pins in [
    ('SYS__U_STOP_LDO','CTRL__U_LDO',{'1':'CONTROL_INPUT_PROTECTED','2':'PACK_RETURN','3':None,'4':None,'5':'CTRL3V3'}),
    ('SYS__C_STOP_IN','CTRL__C_LDO_IN',{'1':'CONTROL_INPUT_PROTECTED','2':'PACK_RETURN'}),
    ('SYS__C_STOP_OUT','CTRL__C_LDO_OUT',{'1':'CTRL3V3','2':'PACK_RETURN'})]:
    p=copy.deepcopy(byref[old]);p.update(reference=new,pins=pins,source_reference=old,source_assembly=str(source.relative_to(ROOT)))
    parts.append(p)
parts.append({'reference':'CTRL__R_PACK_WARN_PU','part':'TNPW060310K0BEEA','value_ohm':10000,
              'pins':{'1':'CTRL3V3','2':'PACK_UV_WARN_N'},
              'note':'Open-drain warning input; a broken input wire reads high and is NOT detected'})
refs={p['reference']:p for p in parts}
checks={
 'no_old_cell_reference':all(n!='CELL_B_MINUS' and not (n or '').startswith('BQ_') for p in parts for n in p['pins'].values()),
 'dedicated_aux_supply':refs['CTRL__U_LDO']['pins']['1']=='CONTROL_INPUT_PROTECTED',
 'watchdog_reset_retained':refs['CTRL__U_WD']['pins']['7']==refs['CTRL__U_HOST']['pins']['6']=='CTRL_HOST_NRST',
 'reset_clears_latch':refs['CTRL__U_PERMIT_LATCH']['pins']['6']==refs['CTRL__U_RESET_BUFFER']['pins']['4'],
 'aux_request_gated':refs['CTRL__U_AUX_GATE']['pins']['2']=='CTRL_LATCH_PERMIT',
 'main_request_gated':refs['CTRL__U_MAIN_GATE']['pins']['2']=='CTRL_LATCH_PERMIT',
 'ldo_enable_not_tied_to_pack':refs['CTRL__U_LDO']['pins']['3'] is None,
}
assert all(checks.values())
result={'status':'pin_mapped_subcircuit_not_integrated_or_qualified','parts':parts,
        'source_sha256':{str(source.relative_to(ROOT)):hashlib.sha256(source.read_bytes()).hexdigest()},
        'external_ports':{
          'CONTROL_INPUT_PROTECTED':'Dedicated input branch AFTER fuse/reverse protection; current limit and faults not yet designed',
          'PACK_RETURN':'Protected pack output negative; do not expose raw cells',
          'PACK_UV_WARN_N':'External open-drain voltage warning; threshold and monitor missing',
          'LOGIC_START_ALLOW':'Candidate replaces former isolator output; rail/partial-power levels not qualified',
          'MAIN_START_ALLOW':'Additional system drive permission; downstream connection not implemented',
          'CTRL_HOST_SWDIO':'Debug port, connector not selected','CTRL_HOST_SWCLK':'Debug port, connector not selected'},
        'checks':checks,'check_scope':'Pin connectivity only; not timing or fault proof',
        'remaining':['Dedicated branch fault protection, thermal/current and capacitance budgets',
                     'Pack undervoltage warning, fresh physical user request input, Tab5 boot/shutdown handshake',
                     'Power-loss/bounce and partially powered output behavior; latch clear timing',
                     'Main permission AND into existing drive rearm; no replacement of independent stop',
                     'New firmware state machine, watchdog timing and layout'],
        'electrically_operational':False,'manufacturing_release':False}
(OUT/'assembly.json').write_text(json.dumps(result,indent=2)+'\n')
with (OUT/'bom.csv').open('w') as f:
    w=csv.writer(f);w.writerow(['reference','part']);w.writerows((p['reference'],p['part']) for p in parts)
with (OUT/'connections.csv').open('w') as f:
    w=csv.writer(f);w.writerow(['reference','pin','net']);w.writerows((p['reference'],pin,n or '') for p in parts for pin,n in p['pins'].items())
print(json.dumps({'part_count':len(parts),'checks':checks}))
