"""Fixed parts' conditional threshold budgets, without lifetime approval."""
import itertools,json
from pathlib import Path
p=Path('validation/brake_divider_parts_v1')
plan=json.loads((p/'plan.json').read_text())
base=json.loads(Path('validation/brake_detector_selection_v1/plan.json').read_text())
a=base['assumptions']; delta=max(abs(t-plan['reference_temperature_C']) for t in plan['temperature_comparison_C'])
rows=[]
for name,age in [('fresh_temperature',0),('general_mode_8000h_comparison',plan['load_life_comparison_fraction'])]:
    # Independent sign envelopes: no assumed tracking between separate resistors.
    factors=[(1+s0*plan['initial_tolerance'])*(1+s1*delta*plan['tcr_per_K'])*(1+s2*age) for s0,s1,s2 in itertools.product((-1,1),repeat=3)]
    bounds={}
    for edge,thresholds in [('rise',(0.396,0.404)),('fall',(0.387,0.400))]:
        vs=[v*(1+a['Rtop_ohm']*ft/(a['Rbottom_ohm']*fb))+sg*a['input_bias_comparison_A']*a['Rtop_ohm']*ft for v,ft,fb,sg in itertools.product(thresholds,(min(factors),max(factors)),(min(factors),max(factors)),(-1,1))]
        bounds[edge]=[min(vs),max(vs)]
    rows.append({'case':name,'threshold_V':bounds,'normal_margin_V':bounds['fall'][0]-5.25,'upper_margin_V':6-bounds['rise'][1]})
result={'rows':rows,'temperature_and_lifetime_qualified':False,'transient_protection_verified':False}
(p/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
