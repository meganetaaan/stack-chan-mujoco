"""Apply predeclared convergence gates to two sparse-contact result reports."""
import argparse,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);a=p.parse_args();plan=json.loads((a.source/'comparison_plan.json').read_text());b=json.loads((Path(plan['baseline'])/'report.json').read_text());v=json.loads((Path(plan['variant'])/'report.json').read_text());changes={'pressure':abs(v['maximum_pressure_MPa']/b['maximum_pressure_MPa']-1)};gates={'pressure':changes['pressure']<=plan['relative_pressure_change_max']}
for part in ['boss','spacer']:
 for kind,key in [('stress','max_absolute_principal_MPa'),('displacement','max_displacement_mm')]:
  label=part+'_'+kind;changes[label]=abs(v['parts'][part][key]/b['parts'][part][key]-1);gates[label]=changes[label]<=plan['relative_'+kind+'_change_max']
r={'relative_changes':changes,'gates':gates,'both_case_numerical_gates_pass':all(b['gates'].values()) and all(v['gates'].values()),'joint_verified':False};(a.source/'comparison.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
