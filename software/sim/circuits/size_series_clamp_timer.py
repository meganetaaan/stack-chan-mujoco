"""LT4363 timer screening at the existing constant-fault operating point."""
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--sense-report',type=Path);a=p.parse_args()
path=Path('validation/series_clamp_sizing_v1/report.json');r=json.loads(path.read_text())
power=r['pass_FET_power_requirement_comparison_W']
sources={str(path):hashlib.sha256(path.read_bytes()).hexdigest()}
if a.sense_report:
 sense=json.loads(a.sense_report.read_text())
 assert sense['source_sha256'][str(path)]==sources[str(path)], 'Sense result uses a different clamp design'
 power=sense['updated_pass_FET_power_comparison_W']
 sources[str(a.sense_report)]=hashlib.sha256(a.sense_report.read_bytes()).hexdigest()
vds=12.6-r['clamp_comparison_V'][0]
# Application-text typical approximation, not interpolation of guaranteed limits.
iov=(4+(50-4)*(vds-.5)/(75-.5))*1e-6
assert .5<=vds<=75
rows=[]
for c in [10e-9,12e-9]:
 warning=c*.1/6e-6;first=c*.775/iov;t=first+warning
 rows.append({'capacitance_F':c,'typical_pre_warning_s':first,'typical_warning_s':warning,
 'typical_total_regulation_s':t,'constant_fault_energy_comparison_J':power*t,
 'typical_cooldown_s':c*6.725/2e-6,'SHDN_low_to_interrupt_cooldown_application_formula_s':c*1e6})
report={'source_sha256':sources,'fault_power_comparison_W':power,
 'datasheet':{'url':'https://www.analog.com/media/en/technical-documentation/data-sheets/4363fb.pdf','revision':'C','sections':'Fault Timer Overview / Operation in Overvoltage / Cool Down Phase; electrical characteristics'},
 'comparison_VDS_V':vds,'typical_interpolated_OV_current_A':iov,'rows':rows,
 'candidate_capacitance':{'nominal_F':12e-9,'proposed_total_tolerance_fraction':.05,'minimum_F':11.4e-9,'part_selected':False,'reason':'Keeps lower capacitance above stated 10 nF minimum; tolerance is a design target, not a purchased component guarantee.'},
 'electrical_table_warning_current_A':[3e-6,5e-6,7e-6],
 'application_text_warning_current_A':6e-6,
 'decision':'Do not select FET using a microsecond pulse rating or choose less than 10 nF to force a pass. Check millisecond linear SOA and a valid worst-case timer bound before integration.',
 'remaining':['Typical interpolated current is not a guaranteed current at actual VCC-OUT.',
 'Electrical table warning current typical 5 uA and application equation 6 uA differ; retain both, do not pick faster value as a guarantee.',
 'Capacitance temperature and bias/leakage must be included in total tolerance.',
 'Gate-discharge delay and pre-regulation transient are outside these times.',
 'OV/current-limit transition and startup require separate cases.',
 '12.6 V fault and constant power are existing comparison conditions, not a transient upper bound.'],
 'timer_selected':False,'SOA_verified':False,'manufacturing_release':False}
a.out.mkdir(parents=True,exist_ok=False);(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(rows))
