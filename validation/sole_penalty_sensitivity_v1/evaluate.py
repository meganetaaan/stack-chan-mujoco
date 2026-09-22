from pathlib import Path
import json
p=Path(__file__).resolve().parent;root=p.parents[1];plan=json.loads((p/'plan.json').read_text());b=json.loads((root/plan['baseline']/'report.json').read_text());rows=[]
for case in ['low','high']:
 r=json.loads((p/case/'report.json').read_text());changes={'pressure':abs(r['maximum_pressure_MPa']/b['maximum_pressure_MPa']-1)}
 for part in ['boss','spacer']:
  for kind,key in [('stress','max_absolute_principal_MPa'),('displacement','max_displacement_mm')]:changes[part+'_'+kind]=abs(r['parts'][part][key]/b['parts'][part][key]-1)
 gates={name:value<=plan['criteria']['relative_'+name.split('_')[-1]+'_change'] for name,value in changes.items()}
 rows.append({'case':case,'relative_changes':changes,'sensitivity_gates':gates,'numerical_gates_pass':all(r['gates'].values())})
(p/'comparison.json').write_text(json.dumps({'rows':rows,'joint_verified':False},indent=2)+'\n');print(json.dumps(rows,indent=2))
