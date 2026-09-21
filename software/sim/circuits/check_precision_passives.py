"""Nominal setting arithmetic and capacitor accounting, not converter qualification."""
import argparse,json,hashlib
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();s=Path('schematics/power/precision_passives_candidate.json');d=json.loads(s.read_text());r=d['RT'];R=r['value_ohm']/1000;t=r['initial_tolerance'];f=16.4/(R+.633)
c=d['COUT'];nom=c['count_each_module']*c['nominal_each_uF'];required=c['required_effective_total_uF'];assert 500<=f*1000<=1400
report={'source_sha256':hashlib.sha256(s.read_bytes()).hexdigest(),'nominal_frequency_MHz':f,'frequency_MHz_resistor_initial_tolerance_only':[16.4/(R*(1+t)+.633),16.4/(R*(1-t)+.633)],'oscillator_total_range_verified':False,'nominal_COUT_uF':nom,'required_effective_COUT_uF':required,'required_combined_capacitance_retention':required/nom,'required_retention_after_initial_minus20percent_sensitivity':required/(nom*.8),'initial20percent_is_sensitivity_not_supplier_qualification':True,'local_COUT_upstream_of_disconnection':True,'capacitor_qualification':False,'manufacturing_release':False}
a.out.mkdir(parents=True,exist_ok=True);(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
