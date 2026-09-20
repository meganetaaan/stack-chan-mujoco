"""Compare unchanged local geometry with reversed master/slave designation."""
import argparse,json,hashlib
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);a=p.parse_args();root=Path(__file__).resolve().parents[3]
plan=json.loads((a.source/'plan.json').read_text());old=root/plan['baseline']/'evaluation.json';new=a.source/'reversed/evaluation.json';before=json.loads(old.read_text());after=json.loads(new.read_text());rows=[]
for name in ('BOOT','YOKE'):
 delta=abs(after['max_displacement_mm'][name]/before['max_displacement_mm'][name]-1);limit=plan['criteria']['displacement_relative_change']
 rows.append({'quantity':'max_displacement_mm','part':name,'relative_change':delta,'limit':limit,'passed':delta<=limit})
delta=abs(after['pressure_max_MPa']/before['pressure_max_MPa']-1);limit=plan['criteria']['peak_pressure_relative_change'];rows.append({'quantity':'pressure_max_MPa','before':before['pressure_max_MPa'],'after':after['pressure_max_MPa'],'relative_change':delta,'limit':limit,'passed':delta<=limit})
r={'comparisons':rows,'source_sha256':{str(f.resolve().relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in (old,new)},'sensitivity_pass':all(x['passed'] for x in rows) and before['local_numerical_probe_pass'] and after['local_numerical_probe_pass'],'joint_strength_verified':False}
(a.source/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
