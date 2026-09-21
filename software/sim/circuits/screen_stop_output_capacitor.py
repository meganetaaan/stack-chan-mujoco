"""Bound what nominal capacitor specifications can prove; no bias curve invented."""
import argparse,json,math
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
r=json.loads(Path('schematics/power/stop_output_capacitor_requirements.json').read_text())
c=r['candidate']['nominal_F'];tol=r['candidate']['initial_tolerance']
# Temperature rating is no-bias, and multiplicative budgeting is an engineering
# screening convention, not a guarantee of joint extreme performance.
initial=c*(1-tol);temp_screen=initial*(1-.15)
result={'part':'GRM31CR71H475KA12L','initial_min_F':initial,
 'initial_temperature_comparison_F':temp_screen,
 'required_remaining_capacitance_factor_for_design_target':2.2e-6/temp_screen,
 'unallocated_fraction_for_bias_ageing_process':1-2.2e-6/temp_screen,
 'DF_test_frequency_Hz':1000,'DF_test_frequency_min_Hz':900,
 'DF_max':.025,'DF_derived_ESR_upper_at_test_ohm':.025/(2*math.pi*900*initial),
 'ESR_upper_limit_ohm':.2,
 'nominal_spec_sufficient_to_prove_ESR':False,
 'actual_ESR_failure_proven':False,
 'bias_ageing_process_qualified':False,
 'limits':['Multiplicative capacitance bookkeeping only; joint extremes not guaranteed',
 'DF bound applies at room temperature and specified AC test conditions, not regulator loop frequencies',
 'A loose ESR upper bound exceeding 0.2 ohm is not evidence actual ESR exceeds 0.2 ohm'],
 'manufacturing_release':False}
(a.out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
