"""Screen a catalog-coded shunt candidate including component TCR."""
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
path=Path('validation/series_clamp_sizing_v1/report.json');r=json.loads(path.read_text())
spec={'manufacturer':'Vishay Dale','candidate_part':'WSLP25128L200FEA','part_basis':'Constructed from manufacturer ordering table; availability not verified.',
 'source':'https://www.vishay.com/docs/30122/wslp.pdf','source_revision':'09-Sep-2024','resistance_ohm':.0082,
 'initial_tolerance_fraction':.01,'component_TCR_abs_ppm_K':75,'TCR_characterized_temperature_C':[-55,155],
 'resistance_reference_temperature_C':25,'rated_power_at_70C_W':3.,'quantity':2,'status':'candidate_not_integrated'}
span=max(abs(t-25) for t in spec['TCR_characterized_temperature_C']);drift=75e-6*span
lo=.0082*(1-.01)*(1-drift);hi=.0082*(1+.01)*(1+drift)
ilow=.045/hi;ihigh=.055/lo
power=.055**2/lo;normal=r['normal_model_per_leg_A']
report={'source_sha256':{str(path):hashlib.sha256(path.read_bytes()).hexdigest()},'candidate':spec,
 'temperature_scope':'Component temperature screening over datasheet TCR interval; not robot ambient requirement or computed resistor temperature.',
 'resistance_range_ohm':[lo,hi],'current_limit_comparison_A':[ilow,ihigh],
 'normal_model_current_A':normal,'normal_model_below_min_limit':normal<ilow,
 'normal_drop_max_V':normal*hi,'normal_loss_max_W':normal**2*hi,
 'limit_loss_max_W':power,'below_P70_rating':power<3,
 'updated_pass_FET_power_comparison_W':(12.6-r['clamp_comparison_V'][0])*ihigh,
 'old_total_1percent_allocation_supported':False,
 'remaining':['Part ordering code and procurement availability need confirmation.',
 'Board thermal conditions and power derating above 70C unverified; 3W comparison is not thermal qualification.',
 'Ageing solder shift and sense trace parasitics not included; Kelvin routing required.',
 'LT4363 sense threshold applicability at all operating states remains unresolved.',
 'Update timer/SOA comparison with increased current before integrating branch.'],
 'manufacturing_release':False}
assert report['normal_model_below_min_limit']
a.out.mkdir(parents=True,exist_ok=False);(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ['resistance_range_ohm','current_limit_comparison_A','limit_loss_max_W','updated_pass_FET_power_comparison_W']}))
