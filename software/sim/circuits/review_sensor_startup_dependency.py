"""Find cold-start dependency deadlock; not a hardware state machine."""
import json
from pathlib import Path
p=Path('validation/brake_sensor_startup_dependency_v1')
plan=json.loads((p/'plan.json').read_text())
results=[]
for upstream in (False,True):
    rules=[({'protected_input_available','main_source_closed'},'servo_bus_available'),
           ({'protected_input_available' if upstream else 'servo_bus_available'},'sensor_supply_available'),
           ({'sensor_supply_available'},'sensor_valid_after_settling'),
           ({'sensor_valid_after_settling','manual_enable_request','protected_input_available'},'main_source_closed')]
    facts=set(plan['initial_facts'])|{'manual_enable_request'}
    trace=[]
    while True:
        added={output for required,output in rules if required<=facts}-facts
        if not added:break
        facts |= added;trace.append(sorted(added))
    results.append({'sensor_supply':'protected_upstream' if upstream else 'servo_bus',
                    'reachable':sorted(facts),'trace':trace,
                    'can_reach_main_source_closed':plan['required_terminal_fact'] in facts})
report={'cases':results,'electrical_startup_verified':False,'decision':'Move sensor LDO inputs upstream of main disconnect; keep brake detector and gate driver downstream'}
(p/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
