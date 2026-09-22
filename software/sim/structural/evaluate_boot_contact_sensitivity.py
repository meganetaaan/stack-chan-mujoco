"""Compare predeclared local contact mesh and penalty sensitivity criteria."""
import argparse,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);a=p.parse_args()
plan=json.loads((a.source/'plan.json').read_text());rows=[];cases={}
for h in plan['mesh_mm']:
 for k in plan['penalty_N_mm3']:
  folder=a.source/f'h{h}_k{k}';r=json.loads((folder/'evaluation.json').read_text());cases[h,k]=r
  rows.append({'mesh_mm':h,'penalty_N_mm3':k,**r})
comparisons=[]
for k in plan['penalty_N_mm3']:
 for key,limit in [('max_displacement_mm',plan['criteria']['last_mesh_displacement_relative']),('pressure_max_MPa',plan['criteria']['last_mesh_peak_pressure_relative'])]:
  value=abs(cases[.5,k][key]/cases[.7,k][key]-1)
  comparisons.append({'kind':'mesh','penalty_N_mm3':k,'quantity':key,'relative_change':value,'limit':limit,'passed':value<=limit})
value=abs(cases[.5,100000]['max_displacement_mm']/cases[.5,10000]['max_displacement_mm']-1)
comparisons.append({'kind':'penalty','quantity':'max_displacement_mm','relative_change':value,'limit':plan['criteria']['fine_mesh_penalty_displacement_relative'],'passed':value<=plan['criteria']['fine_mesh_penalty_displacement_relative']})
r={'rows':rows,'comparisons':comparisons,'all_local_numerical_gates_pass':all(x['local_contact_probe_pass'] for x in rows) and all(x['passed'] for x in comparisons),'joint_strength_verified':False}
(a.source/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'comparisons':comparisons,'all_local_numerical_gates_pass':r['all_local_numerical_gates_pass']},indent=2))
