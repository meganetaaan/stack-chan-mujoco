"""Derive the remaining shunt measurement error budget from model load and IC threshold."""
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
path=Path('validation/series_sense_resistor_v1/report.json');r=json.loads(path.read_text())
clamp=Path('validation/series_clamp_sizing_v1/plan.json');c=json.loads(clamp.read_text())
load=r['normal_model_current_A'];rmax=r['resistance_range_ohm'][1];threshold=min(c['sense_test_range_V'])
headroom=threshold-load*rmax;req=headroom/load
assert headroom>0
report={'sources_sha256':{str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in [path,clamp]},
 'load_current_A':load,'sense_resistance_max_ohm':rmax,'threshold_min_comparison_V':threshold,
 'remaining_positive_error_budget_V':headroom,'equivalent_shared_resistance_budget_ohm':req,
 'acceptance_inequality':'I_load * R_shared + V_other_positive < remaining_positive_error_budget_V',
 'interpretation':'Boundary at the existing maximum model load, not an allocated design margin. All omitted positive measurement errors share this budget.',
 'layout_requirements':['Route SNS and OUT sensing from opposite shunt terminals as independent Kelvin traces.',
 'Do not pick up sense voltage beyond a connector, via chain or common load-current trace.',
 'Include shared pad copper and terminal pickup resistance, IC sense input current voltage drop, thermal EMF and residual ageing/solder shifts.',
 'Record routing and resistor terminal pickup geometry before claiming the budget is met.'],
 'negative_error_scope':'Negative measurement error can increase maximum current and MOSFET stress; it must be bounded separately, not cancelled against positive errors.',
 'unresolved':['Actual layout extraction','Other measurement errors','IC threshold applicability','Load-model coverage of real servo peaks'],
 'routing_qualified':False,'manufacturing_release':False}
a.out.mkdir(parents=True,exist_ok=False);(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'error_budget_mV':headroom*1000,'equivalent_shared_resistance_mOhm':req*1000}))
