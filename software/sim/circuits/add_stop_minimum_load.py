"""Provide a defined minimum load for the TPS709 load-regulation specification."""
import argparse,copy,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
src=Path('schematics/power/servo_power_rearm_integration_revB/assembly.json')
r=copy.deepcopy(json.loads(src.read_text()))
resistance=30100.;tol=.01;vmin=3.207;vmax=3.393
imin=vmin/(resistance*(1+tol));imax=vmax/(resistance*(1-tol));power=vmax*imax
assert imin>100e-6
r['parts'].append({'reference':'R_STOP_MIN_LOAD','part':None,'value_ohm':resistance,'total_tolerance_budget':tol,'pins':{'1':'STOP_AUX3V3','2':'GND'},'note':'Minimum loading; exact resistor and temperature budget pending'})
r['part_count']=len(r['parts']);r['pin_count']=sum(len(x['pins']) for x in r['parts'])
r['scope']='Stop auxiliary supply with explicit minimum load; electrical qualification incomplete'
r['source_sha256']={str(src):hashlib.sha256(src.read_bytes()).hexdigest()}
r['integration_limitations'].append('Minimum load resistor added; rated part and temperature tolerance not selected. No guarantee of total load or transient output.')
(a.out/'assembly.json').write_text(json.dumps(r,indent=2)+'\n')
report={'resistance_ohm':resistance,'total_tolerance_assumption':tol,'supply_interval_assumption_V':[vmin,vmax],
 'minimum_current_A':imin,'maximum_current_A':imax,'maximum_resistor_power_W':power,
 'TPS709_load_regulation_test_minimum_A':100e-6,'conditional_minimum_load_pass':True,
 'supply_interval_basis':'3.3 V +/- (1% DC accuracy +10mV line +50mV load); subject to datasheet test conditions and validity of full load range',
 'datasheet':'https://www.ti.com/lit/ds/symlink/tps709.pdf','source_revision':'SBVS186H table 6.5',
 'total_stop_supply_load_qualified':False,'manufacturing_release':False}
(a.out/'minimum_load_report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
