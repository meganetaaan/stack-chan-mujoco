"""Fixed-divider initial-tolerance screen; not full circuit qualification."""
import itertools
import json
from pathlib import Path
p=Path('validation/brake_detector_selection_v1')
plan=json.loads((p/'plan.json').read_text())
a=plan['assumptions']
rows={}
for name, limits in [('rising',(0.396,0.404)),('falling',(0.387,0.400))]:
    values=[]
    for v,ts,bs,sign in itertools.product(limits,(-1,1),(-1,1),(-1,1)):
        top=a['Rtop_ohm']*(1+ts*a['resistor_initial_tolerance'])
        bottom=a['Rbottom_ohm']*(1+bs*a['resistor_initial_tolerance'])
        values.append(v*(1+top/bottom)+sign*a['input_bias_comparison_A']*top)
    rows[name]={'min_V':min(values),'max_V':max(values)}
result={'threshold_comparison':rows,
        'falling_min_margin_above_normal_max_V':rows['falling']['min_V']-plan['criteria']['normal_max_V'],
        'rising_max_margin_below_servo_max_V':plan['criteria']['servo_max_V']-rows['rising']['max_V'],
        'resistor_tcr_aging_qualified':False,'output_interface_qualified':False,
        'transient_protection_verified':False}
(p/'report.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
