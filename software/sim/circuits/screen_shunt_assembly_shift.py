"""Compare published solder-heat resistance-change limit with remaining sense budget."""
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
paths=[Path('validation/series_sense_resistor_v1/report.json'),Path('validation/series_sense_routing_v1/report.json')]
r,b=[json.loads(x.read_text()) for x in paths]
assert b['sources_sha256'][str(paths[0])]==hashlib.sha256(paths[0].read_bytes()).hexdigest()
# Use highest initial value for the percentage term, then temperature-scale the post-test value.
c=r['candidate'];nom=c['resistance_ohm'];tol=c['initial_tolerance_fraction']
initial_max=nom*(1+tol);initial_min=nom*(1-tol)
heat_shift_max=.005*initial_max+.0005
thermal_factor_max=r['resistance_range_ohm'][1]/initial_max
thermal_factor_min=r['resistance_range_ohm'][0]/initial_min
lo=(initial_min-heat_shift_max)*thermal_factor_min
hi=(initial_max+heat_shift_max)*thermal_factor_max
load=b['load_current_A'];remaining=b['threshold_min_comparison_V']-load*hi
out={'sources_sha256':{str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in paths},
 'source':'https://www.vishay.com/docs/30122/wslp.pdf','source_revision':'09-Sep-2024',
 'published_test':'Resistance to solder heat: +260 C solder, 10 to 12 s dwell, 25 mm/s emergence; change limit +/-(0.5% + 0.0005 ohm).',
 'scope':'Conditional transfer of this published test change to assembly comparison. Actual SMT reflow profile equivalence is not established.',
 'solder_test_shift_used_ohm':heat_shift_max,'post_shift_temperature_range_ohm':[lo,hi],
 'current_limit_comparison_A':[.045/hi,.055/lo],
 'remaining_positive_measurement_budget_V':remaining,'equivalent_remaining_shared_resistance_ohm':remaining/load,
 'prior_budget_consumed_fraction':1-remaining/b['remaining_positive_error_budget_V'],
 'model_load_below_min_limit':remaining>0,'manufacturing_release':False,
 'decision':'Keep shunt as candidate only. Do not use the pre-assembly 3.88 mV budget as a routed-board guarantee.',
 'remaining':['SMT process applicability','Kelvin extraction and other sense errors','Lifetime/environment change not allocated','IC threshold conditions','Updated negative-error FET stress']}
a.out.mkdir(parents=True,exist_ok=False);(a.out/'report.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:out[k] for k in ['current_limit_comparison_A','remaining_positive_measurement_budget_V','prior_budget_consumed_fraction']}))
