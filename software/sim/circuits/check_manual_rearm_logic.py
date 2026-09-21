"""Abstract hardware behavior specification; not robot control firmware."""
import itertools,json
from pathlib import Path
p=Path('validation/manual_rearm_logic_v1')
states=('WAIT_RELEASE','READY','ENABLED')
def step(state,power,monitor,fault,stop,button):
    if not power or not monitor or fault or stop:
        return 'WAIT_RELEASE'
    if state=='WAIT_RELEASE':
        return 'WAIT_RELEASE' if button else 'READY'
    if state=='READY':
        return 'ENABLED' if button else 'READY'
    return 'ENABLED'
rows=[]
for state in states:
    for inputs in itertools.product((False,True),repeat=5):
        power,monitor,fault,stop,button=inputs
        new=step(state,*inputs)
        healthy=power and monitor and not fault and not stop
        assert healthy or new=='WAIT_RELEASE'
        if new=='ENABLED' and state!='ENABLED':
            assert state=='READY' and healthy and button
        if state=='WAIT_RELEASE' and button:
            assert new=='WAIT_RELEASE'
        rows.append({'state':state,'inputs':dict(zip(('power_valid','monitor_valid','fault','stop','button'),inputs)),'next':new,'enable':new=='ENABLED'})
traces={
 'held_button_power_cycle':[(0,0,0,0,1),(1,1,0,0,1),(1,1,0,0,1),(1,1,0,0,0),(1,1,0,0,1),(0,0,0,0,1),(1,1,0,0,1)],
 'fault_clear_while_held':[(1,1,0,0,0),(1,1,0,0,1),(1,1,1,0,1),(1,1,0,0,1),(1,1,0,0,0),(1,1,0,0,1)],
 'release_during_fault_is_not_rearm':[(1,1,1,0,0),(1,1,0,0,1),(1,1,0,0,0),(1,1,0,0,1)]}
expected={'held_button_power_cycle':[False,False,False,False,True,False,False],'fault_clear_while_held':[False,True,False,False,False,True],'release_during_fault_is_not_rearm':[False,False,False,True]}
results={}
for name,inputs_list in traces.items():
    state='WAIT_RELEASE';observed=[]
    for inputs in inputs_list:
        state=step(state,*inputs);observed.append(state=='ENABLED')
    assert observed==expected[name],name
    results[name]={'inputs':inputs_list,'enable':observed}
(p/'report.json').write_text(json.dumps({'transitions_checked':len(rows),'logic_checks_pass':True,'hardware_qualified':False,'transitions':rows,'traces':results},indent=2)+'\n')
print(json.dumps({'transitions_checked':len(rows),'trace_count':len(results),'logic_checks_pass':True,'hardware_qualified':False}))
