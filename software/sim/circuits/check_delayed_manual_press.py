"""Timed counterexample to unqualified debounce-to-DFF rearm wiring."""
import json
from pathlib import Path
p=Path('validation/manual_rearm_delayed_press_v1')
# Clean physical edges; no bounce is needed for this failure.
# At 10 ms, press during fault; fault clears at 20 ms; debounced edge at 60 ms.
trace=[{'time_ms':0,'fault':True,'raw_pressed':False,'debounced_pressed':False},
       {'time_ms':10,'fault':True,'raw_pressed':True,'debounced_pressed':False},
       {'time_ms':20,'fault':False,'raw_pressed':True,'debounced_pressed':False},
       {'time_ms':60,'fault':False,'raw_pressed':True,'debounced_pressed':True}]
q=False;previous=False
for row in trace:
    if row['fault']:q=False
    elif row['debounced_pressed'] and not previous:q=True
    row['single_ff_enable']=q
    previous=row['debounced_pressed']
assert trace[-1]['single_ff_enable']
assert all(r['raw_pressed'] for r in trace if r['time_ms']>=10)
report={'trace':trace,'debounce_ms':50,'fresh_physical_press_after_fault_clear':False,
        'single_ff_implementation_satisfies_rearm_requirement':False,
        'physical_device_fault_test':False}
(p/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
