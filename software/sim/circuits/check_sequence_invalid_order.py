"""Regression for inconsistent latch and reset observations before power enable."""
import argparse,json,itertools
from dataclasses import asdict
from pathlib import Path
from power_sequence_model import Inputs,State,outputs,advance
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(exist_ok=False,parents=True)
def event(armed=True,permission=True,clr=False):
 return Inputs(True,True,True,True,True,armed,permission,clr,False,False)
s=State('WAIT_NEW_PRESS',permission_low_seen=True)
first=advance(s,event(armed=False));second=advance(first,event())
assert first.phase==second.phase=='CLEAR'
assert advance(s,event(clr=True)).phase=='CLEAR'
checks=0
for phase in ('START','RUN'):
 for armed,clr in itertools.product((False,True),repeat=2):
  i=event(armed=armed,clr=clr);o=outputs(State(phase),i);n=advance(State(phase),i)
  if not armed or clr:assert not o.enable_request and n.phase=='CLEAR'
  checks+=1
# A valid fresh permission after a Low remains usable.
waiting=advance(State('WAIT_NEW_PRESS'),event(armed=False,permission=False))
assert advance(waiting,event()).phase=='START'
report={'contradictory_permission_clears':True,'asserted_reset_inhibits':True,
 'operating_cases_checked':checks,'valid_start_preserved':True,
 'trace_after_early_permission':[asdict(first),asdict(second)],
 'hardware_verified':False,'limitations':['Does not prove reset recovery time','Independent observation qualification and asynchronous fault capture still required']}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
