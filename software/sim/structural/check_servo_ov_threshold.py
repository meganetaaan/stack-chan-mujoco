"""LTC4365 OV divider screening, including the specified delay overdrive."""
import argparse,itertools,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
# Comparison values, not released part numbers or whole-life tolerances.
rhi,rlo,tol=100000.,10000.,.001
rows=[]
for hi,lo,ref,leak in itertools.product([rhi*(1-tol),rhi*(1+tol)],[rlo*(1-tol),rlo*(1+tol)],[.4925,.5075],[-10e-9,10e-9]):
 gain=1+hi/lo
 rows.append({'Rhigh_ohm':hi,'Rlow_ohm':lo,'reference_V':ref,'input_leakage_A':leak,'trip_V':ref*gain+leak*hi,'voltage_for_50mV_overdrive_V':(ref+.05)*gain+leak*hi})
r={'comparison_resistors_ohm':[rhi,rlo],'assumed_resistor_tolerance_fraction':tol,'resistor_part_numbers':None,'source':'https://www.analog.com/media/en/technical-documentation/data-sheets/ltc4365.pdf','source_conditions':'OV threshold 492.5..507.5mV; leakage +/-10nA specified at pin0.5V VIN34V; delay specified at 50mV overdrive VIN=VOUT=12V','trip_range_V':[min(x['trip_V'] for x in rows),max(x['trip_V'] for x in rows)],'worst_voltage_for_specified_overdrive_V':max(x['voltage_for_50mV_overdrive_V'] for x in rows),'corners':rows,'qualified':False,'decision':'Static threshold separation alone is insufficient: specified delay overdrive may occur only above 6V; do not transfer 12V delay specification to 5V operation','exclusions':['Resistor temperature drift ageing voltage coefficient','Guaranteed leakage away from stated test point','FET charge turnoff and bus transients','UV divider startup hysteresis and manual rearm']}
(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(r['trip_range_V'],r['worst_voltage_for_specified_overdrive_V'])
