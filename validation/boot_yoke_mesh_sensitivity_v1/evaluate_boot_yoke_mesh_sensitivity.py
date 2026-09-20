"""Evaluate predeclared mesh sensitivity of the deformable local joint."""
import argparse,json,hashlib
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);a=p.parse_args();root=Path(__file__).resolve().parents[3]
plan=json.loads((a.source/'plan.json').read_text());middle=root/plan['middle_source']/'evaluation.json'
paths={1:a.source/'h1/evaluation.json',.7:middle,.5:a.source/'h0.5/evaluation.json'}
cases={h:json.loads(f.read_text()) for h,f in paths.items()};comparisons=[]
for part in ('BOOT','YOKE'):
 change=abs(cases[.5]['max_displacement_mm'][part]/cases[.7]['max_displacement_mm'][part]-1)
 comparisons.append({'quantity':'max_displacement_mm','part':part,'relative_change':change,'limit':plan['criteria']['last_displacement_relative_change'],'passed':change<=plan['criteria']['last_displacement_relative_change']})
change=abs(cases[.5]['pressure_max_MPa']/cases[.7]['pressure_max_MPa']-1)
comparisons.append({'quantity':'pressure_max_MPa','relative_change':change,'limit':plan['criteria']['last_peak_pressure_relative_change'],'passed':change<=plan['criteria']['last_peak_pressure_relative_change']})
r={'source_sha256':{str(f.resolve().relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in paths.values()},'rows':[{'mesh_mm':h,**case} for h,case in cases.items()],'comparisons':comparisons,'all_numerical_gates_pass':all(x['passed'] for x in comparisons) and all(x['local_numerical_probe_pass'] for x in cases.values()),'joint_strength_verified':False}
(a.source/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'comparisons':comparisons,'all_numerical_gates_pass':r['all_numerical_gates_pass']},indent=2))
