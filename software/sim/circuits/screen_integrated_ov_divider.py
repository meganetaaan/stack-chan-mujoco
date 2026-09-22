"""Static OV divider and pin-voltage screening; does not prove transient cutoff."""
import argparse,itertools,json,hashlib
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
source=Path('schematics/power/integrated_servo_protection_screen.json');spec=json.loads(source.read_text())
rh,rl,tol=35700.,10000.,.001
rows=[]
for hi,lo,ref,leak in itertools.product([rh*(1-tol),rh*(1+tol)],[rl*(1-tol),rl*(1+tol)],spec['OVLO_rising_range_V'],[-spec['OVLO_leakage_max_abs_A'],spec['OVLO_leakage_max_abs_A']]):
 rows.append({'Rhigh_ohm':hi,'Rlow_ohm':lo,'reference_V':ref,'leak_A':leak,'trip_V':ref*(1+hi/lo)+leak*hi,'pin_at_5_25V':(5.25-leak*hi)/(1+hi/lo),'pin_at_12_6V':(12.6-leak*hi)/(1+hi/lo)})
r={'comparison_resistors_ohm':[rh,rl],'initial_tolerance_fraction':tol,'corners':rows,'trip_range_V':[min(x['trip_V'] for x in rows),max(x['trip_V'] for x in rows)],'pin_at_12_6V_max':max(x['pin_at_12_6V'] for x in rows),'normal_ceiling_assumption_V':5.25,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'qualification':False,'limits':['5.25V is existing normal rail target, not guaranteed regulator output','12.6V is 3S charged-pack feedthrough comparison, not a complete surge bound','Leakage limit applies at pin0.5..1.5V; computed 12.6V case extrapolates and is diagnostic only','Resistor lifetime drift excluded','OVLO timing maximum absent; no 6V transient guarantee']}
(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(r['trip_range_V'],r['pin_at_12_6V_max'])
