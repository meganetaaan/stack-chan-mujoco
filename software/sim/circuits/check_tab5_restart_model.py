"""Adversarial event traces for the Tab5 restart design contract."""
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
from tab5_restart_model import Inputs, State, outputs, advance

ROOT = Path(__file__).resolve().parents[3]
traces = {}
def run(name, events):
    state = State()
    rows = []
    for t, kwargs in events:
        if kwargs.pop('reset', False):
            state = State()
        i = Inputs(**kwargs)
        before = outputs(state, i)
        n = advance(state, i, t)
        after = outputs(n, i)
        assert not after.drive_permission or (i.healthy and i.power_valid and i.ready and not i.stop)
        rows.append(dict(time_ms=t, inputs=asdict(i), before=asdict(before), state=asdict(n), after=asdict(after)))
        state = n
    traces[name] = rows
    return rows

off = dict(off_verified=True)
r = run('early_request_not_deferred', [(0,off.copy()),(4999,dict(off,request=True)),(5000,dict(off,request=True)),(5100,off.copy()),(5101,dict(off,request=True))])
assert [x['state']['phase'] for x in r] == ['OFF','OFF','OFF','OFF','BOOT']
r = run('off_observation_loss_restarts_wait',[(0,off.copy()),(4999,{}),(5000,off.copy()),(9999,dict(off,request=True)),(10000,off.copy()),(10001,dict(off,request=True))])
assert r[3]['state']['phase']=='OFF' and r[-1]['state']['phase']=='BOOT'
r = run('controller_reset_discards_time',[(0,off.copy()),(4999,dict(off,reset=True)),(5000,dict(off,request=True)),(9999,off.copy()),(10000,dict(off,request=True))])
assert r[2]['state']['phase']=='OFF' and r[-1]['state']['phase']=='BOOT'
r = run('backwards_time',[(0,off.copy()),(4999,off.copy()),(10,dict(off,request=True)),(5010,dict(off,request=True))])
assert all(x['state']['phase']=='OFF' for x in r)
r = run('unknown_observation_interval',[(0,off.copy()),(4999,dict(off,continuous_observation=False)),(5000,off.copy()),(5001,dict(off,request=True))])
assert all(x['state']['phase']=='OFF' for x in r)
boot=[(0,off.copy()),(5000,dict(off,request=True))]
ready=dict(power_valid=True,ready=True)
r = run('fresh_arm_and_brownout',boot+[(5001,dict(ready,arm=True)),(5002,dict(ready,arm=True)),(5003,ready.copy()),(5004,dict(ready,arm=True)),(5005,dict(ready,power_valid=False)),(5006,dict(ready,arm=True))])
assert not r[3]['after']['drive_permission'] and r[5]['after']['drive_permission']
assert not r[6]['before']['drive_permission'] and r[-1]['state']['phase']=='OFF'
r = run('shutdown_ack_required',boot+[(5001,ready.copy()),(5002,dict(ready,stop=True)),(99999,ready.copy()),(100000,dict(ready,shutdown_ack=True))])
assert r[-2]['after']['tab5_allow'] and r[-2]['after']['shutdown_request']
assert not r[-1]['after']['tab5_allow']
r = run('fault_overrides_shutdown',boot+[(5001,ready.copy()),(5002,dict(ready,stop=True)),(5003,dict(ready,healthy=False))])
assert not r[-1]['before']['tab5_allow'] and r[-1]['state']['phase']=='OFF'
model=Path(__file__).with_name('tab5_restart_model.py')
report={'model_sha256':hashlib.sha256(model.read_bytes()).hexdigest(),'scenarios':traces,
 'scenario_count':len(traces),'contract_checks_pass':True,'hardware_implemented':False,
 'limits':['off_verified must certify actual off condition; voltage threshold and observation circuit not selected',
 'continuous_observation requires fault capture between samples; no sampled Boolean can prove it',
 'timestamps represent a conservative elapsed-time lower bound; oscillator tolerance/scheduling not modeled',
 'ready and shutdown_ack must be fresh for current boot/transaction',
 'BOOT has no selected deadline: it never permits drive without ready but can remain powered indefinitely',
 'drive_permission must be ANDed with existing independent servo protection; it does not replace it',
 'No detector, GPIO, backfeed, asynchronous timing or internal Tab5 discharge proof'],
 'manufacturing_release':False}
out=ROOT/'validation/tab5_restart_v1';out.mkdir(exist_ok=True)
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print('checked',len(traces),'adversarial scenarios')
