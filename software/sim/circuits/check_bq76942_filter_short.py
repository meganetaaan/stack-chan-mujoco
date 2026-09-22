"""DC single capacitor-short screen, excluding IC clamps and transient effects."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
d=json.loads((ROOT/'schematics/power/bq76942_candidate.json').read_text())
r=d['cell_input_filter_candidate']['resistor']
v=4.2
rv=r['resistance_ohm']*(1-r['initial_tolerance_fraction'])
i=v/(2*rv)
p=i*i*rv
report={
 'scope':'single cell differential capacitor short; stiff 4.2V cell, two equal minimum-initial-tolerance series resistors; excludes IC currents, harness resistance and thermal feedback',
 'R_each_ohm':rv,'current_A':i,'power_each_W':p,
 'P70_general_W':0.110,'P70_power_W':0.170,'P70_advanced_W':0.210,
 'general_rating_exceeded':p>0.110,'power_rating_exceeded':p>0.170,
 'advanced_rating_exceeded':p>0.210,
 'faults':[{'physical_cell':k,'path':f'cell{k} positive -> upper sense resistor -> shorted capacitor -> lower sense resistor -> cell{k} negative','stopped_by_main_CHG_DSG':False,'passes_main_pack_shunt':False} for k in [1,2,3]],
 'VC0_capacitor_short':'shorts VC0 to local VSS; not a cell discharge loop in this ideal model; sensing effects unqualified',
 'decision':'No thermal qualification from highest catalog rating; independent cell-tap fault protection required even if resistors enlarged',
 'manufacturing_release':False}
(ROOT/'validation/bq76942_filter_short_v1/report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
