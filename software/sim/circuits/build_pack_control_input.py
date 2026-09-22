"""Connect an explicit eFuse candidate to the independent startup controller."""
import copy,csv,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'schematics/power/pack_control_input_candidate_v1';OUT.mkdir(exist_ok=True)
controller=ROOT/'schematics/power/pack_start_controller_candidate_v1/assembly.json'
limiter=ROOT/'schematics/power/bq76942_reg0_limiter_candidate.json'
a=json.loads(controller.read_text());b=json.loads(limiter.read_text())
parts=copy.deepcopy(a['parts'])
bindings={'CELL_POS_FUSED':'PACK_FUSED_REVERSE_PROTECTED','CELL_B_MINUS':'PACK_RETURN',
          'BQ_REG0_LIMITED':'CONTROL_INPUT_PROTECTED'}
for old in b['parts']:
 p=copy.deepcopy(old)
 p['reference']=old['reference'].replace('REG0','CTRL_INPUT')
 p['pins']={pin:bindings.get(n,n.replace('REG0','CTRL_INPUT') if n else None) for pin,n in old['pins'].items()}
 p['source_reference']=old['reference'];p['source_assembly']=str(limiter.relative_to(ROOT))
 parts.append(p)
byref={p['reference']:p for p in parts};assert len(byref)==len(parts)==40
u=byref['U_CTRL_INPUT_LIMIT'];ldo=byref['CTRL__U_LDO']
checks={
 'input_after_external_fuse_reverse_port':u['pins']['8']==u['pins']['9']=='PACK_FUSED_REVERSE_PROTECTED',
 'protected_output_feeds_controller_LDO':u['pins']['23']==u['pins']['24']==ldo['pins']['1']=='CONTROL_INPUT_PROTECTED',
 'common_pack_return':u['pins']['17']==ldo['pins']['2']=='PACK_RETURN',
 'RTN_kept_separate':u['pins']['15']==u['pins']['EP']=='CTRL_INPUT_PROTECT_RTN' and u['pins']['15']!=u['pins']['17'],
 'mode_resistor_to_RTN':byref['R_CTRL_INPUT_MODE']['pins']=={'1':'CTRL_INPUT_MODE','2':'CTRL_INPUT_PROTECT_RTN'},
 'no_direct_input_output_copper':not a.get('interconnects'),
 'startup_controller_supply_not_own_enabled_rail':ldo['pins']['5']=='CTRL3V3',
}
assert all(checks.values())
result={'status':'integrated_input_branch_candidate_not_qualified','parts':parts,
 'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [controller,limiter]},
 'checks':checks,'check_scope':'Explicit pin/net topology only; IC conduction and fault behavior excluded',
 'external_ports':dict(a['external_ports']),
 'mode':'TPS26600 active current limiting with thermal latch-off, MODE402kohm to RTN',
 'nominal_ILIM_A':12/118,
 'nominal_UV_rising_V':1.19*(1+40.2/10),'nominal_UV_falling_V':1.1*(1+40.2/10),
 'nominal_OV_rising_V':1.19*(1+124/10),
 'threshold_scope':'Nominal RTN-referenced values only; not battery-cell protection or tolerance bounds',
 'not_inherited':['Original BQ REG0 emitter-follower load behavior','Original diode/feed resistors','Earlier startup or short-circuit results'],
 'remaining':['Full load and inrush budget versus guaranteed current limit at actual voltage and resistor tolerance',
              'Output ramp with dVdT open and capacitors; do not assume successful startup',
              'Short-circuit energy and thermal latch timing, LDO input-output short and downstream overvoltage',
              'Pack PCM restart and cold/brownout sequencing, manual recovery of a latched input fault',
              'Input transients, fuse coordination and PCB thermal/layout',
              *a['remaining']],
 'electrically_operational':False,'manufacturing_release':False}
result['external_ports'].pop('CONTROL_INPUT_PROTECTED')
result['external_ports']['PACK_FUSED_REVERSE_PROTECTED']='Connect only after system fuse and reverse-input protection; main inlet not integrated here'
(OUT/'assembly.json').write_text(json.dumps(result,indent=2)+'\n')
for filename,header,rows in [
 ('bom.csv',['reference','part'],[(p['reference'],p['part']) for p in parts]),
 ('connections.csv',['reference','pin','net'],[(p['reference'],pin,n or '') for p in parts for pin,n in p['pins'].items()])]:
 with (OUT/filename).open('w',newline='') as f:
  w=csv.writer(f,lineterminator='\n');w.writerow(header);w.writerows(rows)
print(json.dumps({'parts':len(parts),'checks':checks,'nominal_ILIM_A':result['nominal_ILIM_A']}))
