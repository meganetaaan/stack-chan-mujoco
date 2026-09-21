"""Analytic RC design counterexamples; not an IC or battery transient model."""
import json
import math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
a={'pack_V':12.6,'R_ohm':100.0,'C_F':0.001,'stop_delta_V':0.5,
   'poll_s':0.250,'default_timeout_s':0.050,
   'origin':'engineering examples to test entry/exit semantics; R/C are not selected or measured robot values'}
def voltage(t,load):
    steady=a['pack_V']-a['R_ohm']*load
    return max(0.0,steady*(1-math.exp(-t/(a['R_ohm']*a['C_F']))))
rows=[]
for name,load in [('no_load',0),('load_10mA',.010)]:
    steady_delta=a['R_ohm']*load
    target=a['pack_V']-a['stop_delta_V']
    reachable=steady_delta<a['stop_delta_V']
    t=(-a['R_ohm']*a['C_F']*math.log(1-target/(a['pack_V']-steady_delta))) if reachable else None
    rows.append({'case':name,'load_A':load,'voltage_at_default_timeout_V':voltage(a['default_timeout_s'],load),
      'residual_delta_at_default_timeout_V':a['pack_V']-voltage(a['default_timeout_s'],load),
      'default_timeout_can_enable_DSG_without_reaching_delta':True,
      'voltage_exit_reachable':reachable,'ideal_threshold_time_s':t,
      'illustrative_exit_on_250ms_poll_grid_s':math.ceil(t/a['poll_s'])*a['poll_s'] if t is not None else None})
rows.append({'case':'output_short','voltage_V':0,'default_timeout_can_enable_DSG_without_reaching_delta':True,
             'voltage_exit_reachable':False,'zero_timeout_does_not_enable_DSG_from_elapsed_time':True})
report={'scope':'TRM exit semantics and ideal constant-load RC examples, not timing/ADC/FET validation',
 'source':'TI SLUUBY1B 5.2.3.2.2 and13.3.6.5/6','assumptions':a,'cases':rows,
 'load_ceiling_for_voltage_exit_A':a['stop_delta_V']/a['R_ohm'],
 'ceiling_is_strict_inequality':True,
 'conclusion':'Use zero hardware timeout plus voltage condition; implement independent abort and inhibit downstream loads',
 'manufacturing_release':False}
out=ROOT/'validation/bq76942_predischarge_v1';out.mkdir(exist_ok=True)
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
