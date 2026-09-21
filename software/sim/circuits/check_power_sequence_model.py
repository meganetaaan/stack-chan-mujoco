"""Exhaustively check reachable sampled states with independent input combinations."""
import argparse,itertools,json
from dataclasses import asdict
from pathlib import Path
from power_sequence_model import Inputs,State,outputs,advance
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
a.out.mkdir(parents=True,exist_ok=False)
plan={'scope':__doc__,'criteria':['No enable outside START/RUN',
 'Health or permission loss inhibits output without waiting for sampled state update',
 'Either PG failure in RUN inhibits both-leg enable',
 'Startup expiry inhibits and wins simultaneous PG success',
 'Clear completion requires independent latch and fresh hold observations',
 'Fault recovery alone cannot reach START'],
 'limits':['Boolean sampled observations only, not asynchronous timing proof',
 'Manual permission is an externally qualified latch, not a raw button',
 'No latch state or timer acknowledgement is assigned by this model']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
inputs=[Inputs(*v) for v in itertools.product((False,True),repeat=10)]
seen={State()};pending=[State()];count=0
while pending:
 s=pending.pop()
 for i in inputs:
  o=outputs(s,i);n=advance(s,i);count+=1
  assert not o.enable_request or (s.phase in ('START','RUN') and i.healthy and i.permission)
  assert not (s.phase=='RUN' and not(i.left_pg and i.right_pg) and o.enable_request)
  assert not(s.phase=='START' and i.startup_expired and o.enable_request)
  assert not(o.enable_request and o.clear_request)
  if s.phase=='CLEAR' and n.phase!='CLEAR':
   assert s.clear_phase=='QUALIFY' and i.healthy and i.clr_low and i.hold_done and not i.armed and not i.permission
  if n.phase=='START' and s.phase!='START':
   assert s.phase=='WAIT_NEW_PRESS' and s.permission_low_seen and i.permission and i.armed and i.healthy and not i.startup_expired
  if s.phase in ('START','RUN') and not i.healthy:assert n==State()
  if n not in seen:seen.add(n);pending.append(n)
# A normal startup and a right-leg failure, with external observations delayed.
def event(**kw):
 d=dict(independent_health=True,left_source=True,right_source=True,left_pg=False,right_pg=False,
        armed=False,permission=False,clr_low=True,hold_done=False,startup_expired=False)
 d.update(kw);return Inputs(**d)
scenario=[('observe_hold_low',event()),('stale_latch',event(hold_done=True,armed=True)),
 ('clear_ack',event(hold_done=True)),('permission_low_after_release',event(clr_low=False)),
 ('fresh_permission',event(clr_low=False,armed=True,permission=True)),
 ('left_ready_only',event(clr_low=False,armed=True,permission=True,left_pg=True)),
 ('both_ready',event(clr_low=False,armed=True,permission=True,left_pg=True,right_pg=True)),
 ('right_failed',event(clr_low=False,armed=True,permission=True,left_pg=True)),
 ('voltage_recovered_latch_still_high',event(clr_low=False,armed=True,permission=True,left_pg=True,right_pg=True))]
s=State();trace=[]
for name,i in scenario:
 o=outputs(s,i);n=advance(s,i);trace.append({'event':name,'state':asdict(s),'inputs':asdict(i),'outputs':asdict(o),'next':asdict(n)});s=n
assert [x['next']['phase'] for x in trace]==['CLEAR','CLEAR','WAIT_NEW_PRESS','WAIT_NEW_PRESS','START','START','RUN','CLEAR','CLEAR']
assert not trace[-2]['outputs']['enable_request'] and not trace[-1]['outputs']['enable_request']
report={'reachable_states':[asdict(s) for s in sorted(seen,key=repr)],'transitions_checked':count,'trace':trace,
 'sampled_contract_pass':True,'hardware_implemented':False,'physical_timing_proven':False,
 'remaining':['Choose sequencer hardware and implement qualified inputs and timer interfaces',
 'Ensure permission Low-to-High represents a fresh physical release/press with reset recovery timing',
 'Implement asynchronous fault capture: sub-sample pulses are outside this model',
 'Define startup deadline from converter/switch startup and safe fault energy; no arbitrary default deadline',
 'Implement timer reset/freshness at actual pins and load budgets'], 'manufacturing_release':False}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(count,len(seen))
