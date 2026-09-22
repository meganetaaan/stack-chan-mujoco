"""Compare discharge simulations against the saved candidate target and an isolated RC calculation."""
import argparse, json, math
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);a=p.parse_args()
plan=json.loads((a.source/'plan.json').read_text())
r=plan['candidate_each_ohm']*(1+plan['assumed_resistance_tolerance'])
c=plan['assumed_Cout_max_uF']*1e-6;v0=plan['initial_voltage_bound_V']
limit=plan['candidate_requirement']['rail_at_920ms_after_disconnect_max_V']
rows=[]
for case,alive in [('both_working',2),('one_open',1),('both_open',0)]:
    report=json.loads((a.source/case/'report.json').read_text())
    sample=report['samples'][-1]
    assert sample['time_s']==1. and report['numerical_checks_passed']
    isolated=v0*math.exp(-.92/(r/alive*c)) if alive else v0
    rows.append({'case':case,'simulated_rail_V':sample['rail_V'], 'simulated_Cout_energy_J':sample['Cout_energy_J'],
                 'simulation_meets_candidate_target':sample['rail_V']<=limit,
                 'isolated_RC_rail_V':isolated,'isolated_RC_meets_candidate_target':isolated<=limit})
rmin=plan['candidate_each_ohm']*(1-plan['assumed_resistance_tolerance'])
result={'cases':rows,'each_resistor_max_operating_power_W':v0*v0/rmin,
        'total_max_operating_power_W':2*v0*v0/rmin,
        'Cout_initial_energy_bound_J':.5*c*v0*v0,
        'maximum_each_resistance_ohm_for_single_survivor_RC_target':.92/(c*math.log(v0/limit)),
        'protection_design_verified':False,
        'interpretation':'Isolated RC excludes other discharge and energy paths; this comparison exposes dependence on behavioral loads, not a proof of full-circuit worst-case bounds.'}
(a.source/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
