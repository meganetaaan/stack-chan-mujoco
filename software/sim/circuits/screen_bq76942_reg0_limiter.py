"""Conditional resistor stress comparison, not an eFuse macromodel."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
out=ROOT/'validation/bq76942_reg0_limiter_v1';out.mkdir(exist_ok=True)
a=json.loads((ROOT/'schematics/power/bq76942_reg0_limiter_candidate.json').read_text())
r=a['feed_resistors']['each_ohm']
rows=[]
for current in [.020,.100,.120,.250]:
 rows.append({'total_current_A':current,'per_resistor_W':(current/2)**2*r,
              'old_single_resistor_W':current**2*(r/2),
              'feed_drop_V':current*r/2})
report={'scope':'Conditional DC stress only; current values are comparisons, not guaranteed TPS26600 3S limits',
 'rows':rows,'source_current_scope':'TI table 7.5 gives 80..120mA short-circuit current only at RILIM=120kohm and VIN-VOUT=5V; actual candidate uses118kohm and different operating conditions',
 'positive_change':'For a given total current and unchanged22.1ohm equivalent, each resistor dissipates half the former loss',
 'termination_condition':'Compare steady limiting modes and distributed resistor dissipation; do not infer switch transient from nominal timer',
 'remaining':['3S overcurrent bounds at selected RILIM','fast-trip/retry transient stress','thermal latch and fault recovery','input/output capacitor startup','MCU and interface load budget'],
 'manufacturing_release':False}
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(rows,indent=2))
