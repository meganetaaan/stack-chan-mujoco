"""Functional event model of the selected latch/gates, not analog timing proof."""
import argparse,hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parents[3]
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
paths=['schematics/power/bq_host_watchdog_candidate.json','schematics/power/system_power_integration_candidate_v1/assembly.json']
candidate,assembly=[json.loads((root/x).read_text()) for x in paths]
parts={x['reference']:x for x in assembly['parts']}
wd=parts['BAT__U_BQ_WD']['pins'];latch=parts['BAT__U_BQ_PERMIT_LATCH']['pins'];buf=parts['BAT__U_BQ_RESET_BUFFER']['pins']
assert wd['7']==buf['2']==parts['BAT__U_BQ_HOST']['pins']['6']
assert latch['6']==buf['4']
assert latch['2']==latch['7']==latch['8']=='BQ_CTRL3V3'
for name in ['MAIN','AUX']:
 assert parts['BAT__U_BQ_'+name+'_GATE']['pins']['2']==latch['5']=='BQ_LATCH_PERMIT'
assert wd['3']==wd['5']=='BQ_CTRL3V3'
# At valid supply, CLR dominates and releasing CLR alone cannot clock in D.
# WDO and supervisor are ideal open drains here. WDO pulse length is NOT simulated.
def evaluate(events):
 q=None;prev_arm=0;rows=[]
 for label,sup_ok,wd_ok,arm,main,aux,expected in events:
  reset_n=sup_ok and wd_ok
  if not reset_n:q=0
  elif arm and not prev_arm:q=1
  actual=[int(q and main),int(q and aux)] if q is not None else [None,None]
  assert actual==expected,(label,actual,expected)
  rows.append(dict(event=label,supply_supervisor_released=sup_ok,watchdog_released=wd_ok,arm=arm,
    raw_requests=[main,aux],latch_Q=q,outputs=actual,
    direct_WDO_gate_counterfactual=[int(reset_n and main),int(reset_n and aux)]))
  prev_arm=arm
 return rows
cases={
 'frozen_high_requests_and_arm':[
  ('startup_reset',0,1,0,1,1,[0,0]),('supply_valid',1,1,0,1,1,[0,0]),
  ('explicit_arm',1,1,1,1,1,[1,1]),('watchdog_fault',1,0,1,1,1,[0,0]),
  ('watchdog_pulse_ends',1,1,1,1,1,[0,0]),('still_frozen',1,1,1,1,1,[0,0])],
 'new_edge_required':[
  ('reset',0,1,0,1,1,[0,0]),('valid',1,1,0,1,1,[0,0]),
  ('arm',1,1,1,1,1,[1,1]),('fault',1,0,1,1,1,[0,0]),
  ('pulse_ends',1,1,1,1,1,[0,0]),('arm_low',1,1,0,1,1,[0,0]),
  ('new_arm_edge',1,1,1,1,1,[1,1])],
 'arm_during_reset_is_not_deferred':[
  ('reset',0,1,0,1,1,[0,0]),('arm_while_reset',0,1,1,1,1,[0,0]),
  ('reset_released_arm_held',1,1,1,1,1,[0,0])],
 'independent_requests':[
  ('reset',0,1,0,0,0,[0,0]),('valid',1,1,0,0,0,[0,0]),
  ('arm',1,1,1,0,0,[0,0]),('main_only',1,1,0,1,0,[1,0]),
  ('aux_only',1,1,0,0,1,[0,1]),('both',1,1,0,1,1,[1,1]),
  ('brownout',0,1,0,1,1,[0,0]),('recovery',1,1,0,1,1,[0,0])],
}
rows={name:evaluate(events) for name,events in cases.items()}
report={'source_sha256':{x:hashlib.sha256((root/x).read_bytes()).hexdigest() for x in paths},
 'system_part_count':len(parts),'scenarios':rows,'model_scope':'Ideal logic at valid supply. No propagation delays, metastability, ramp, leakage, reset loading, heartbeat waveform or physical fault injection.',
 'automatic_pulse_release_does_not_rearm':True,
 'new_ARM_edge_can_rearm':True,'fresh_user_authorization_path_implemented':False,
 'watchdog_timeout_is_safe_deadline_proven':False,'analog_electrical_qualification':False,'manufacturing_release':False}
a.out.mkdir(parents=True,exist_ok=True);(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(f'{len(rows)} functional scenarios checked; analog/reset/rearm qualification incomplete')
