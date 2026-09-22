"""Budget RESET_N leakage without assuming unpowered CMOS leakage is specified."""
import argparse,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
plan={'question':'What voltage/current budget remains on the shared reset after known fanout?', 'stop':'One DC budget and POR necessary-condition calculation; no assumed transient simulation.', 'assumptions':['3.207..3.393V rail','100k pullup with provisional +/-1% tolerance','1uA per HCS input used as powered endpoint comparison from 6V specification, not unpowered guarantee'],'acceptance':'Do not approve RESET_N without receiver thresholds, external sink leakage, POR load and discharge timing evidence.'}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
rmax,rmin=101000,99000
known=3e-6+.3e-6
rows=[{'external_off_leakage_A':i,'high_voltage_lower_comparison_V':3.207-rmax*(known+i)} for i in [0,1e-6,5e-6,10e-6]]
r={'powered_known_leakage_comparison_A':known,'powered_sourcing_input_load_comparison_A':3e-6,'reset_low_sink_current_upper_without_external_source_A':3.393/rmin+3e-6,'high_cases':rows,'POR_necessary_budget':{'supply_V':.8,'pullup_current_conservative_A':.8/rmin,'total_sink_test_limit_A':15e-6,'remaining_all_other_source_current_A':15e-6-.8/rmin,'note':'Do not subtract powered leakage numbers here: HCS devices below rated supply need separate evidence.'},'full_reset_qualified':False,'pending':['Actual pullup tolerance including temperature','HCS thresholds across actual supply interval','External fault sink leakage/current','Below-rated-supply input behavior','POR supply slew condition','Capacitance and fault pulse duration']}
(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
