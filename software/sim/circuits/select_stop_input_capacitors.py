"""Specify bulk film plus local ceramic input capacitance for stop-supply candidate."""
import argparse,csv,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
base=Path('schematics/power/servo_power_rearm_integration_revL/assembly.json');r=json.loads(base.read_text())
x=next(x for x in r['parts'] if x['reference']=='C_STOP_IN')
assert x['part'] is None and x['value_F']==2.2e-6
x.update(part='MKS2C042201K00JSSD',dielectric='PET film',initial_tolerance=.05,
 rated_voltage_V=63,body_nominal_mm={'width':7.2,'height':13,'length':7.2},lead_pitch_mm=5,
 selection_source='https://www.wima.de/wp-content/uploads/media/e_WIMA_MKS_2.pdf',
 requirement='Input bulk candidate; temperature/process capacitance and board envelope unqualified')
r['parts'].append({'reference':'C_STOP_IN_HF','part':'GRM31C5C1H104JA01L','value_F':1e-7,
 'pins':{'1':'STOP_LDO_INPUT','2':'GND'},'placement':'Directly at TPS709 IN/GND; film bulk does not replace local HF return'})
r.update(part_count=len(r['parts']),pin_count=sum(len(x['pins']) for x in r['parts']),scope=__doc__)
r['source_sha256']={str(base):hashlib.sha256(base.read_bytes()).hexdigest()}
r['integration_limitations'].append('WIMA 2.2uF film input plus 100nF C0G local bypass selected as candidates; 13mm film body height, routing and operating capacitance unqualified')
a.out.mkdir(parents=True,exist_ok=False)
(a.out/'assembly.json').write_text(json.dumps(r,indent=2)+'\n')
with (a.out/'candidate_bom.csv').open('w') as f:
 w=csv.writer(f,lineterminator='\n');w.writerow(['reference','part_candidate','value_ohm','value_F'])
 for x in r['parts']:w.writerow([x['reference'],x['part'],x.get('value_ohm',''),x.get('value_F','')])
# Only initial capacitance tolerance is used, not a fabricated full-temperature bound.
lo=2.2e-6*.95+1e-7*.95;hi=2.2e-6*1.05+1e-7*1.05
report={'source_revision':'WIMA 03.26 pp34-35','initial_total_capacitance_F':[lo,hi],
 'RC_initial_comparison_s':[990*lo,1010*hi],
 'max_initial_stored_energy_at_12V6_J':.5*hi*12.6**2,
 'voltage_rating_comparison_pass':12.6<63 and 12.6<50,
 'whole_temperature_capacitance_bounded':False,'startup_time_proven':False,
 'PCB_height_fit_proven':False,'manufacturing_release':False,
 'note':'RC time constant excludes LDO and bleed load and diode nonlinearity; not a start deadline'}
(a.out/'selection_report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
