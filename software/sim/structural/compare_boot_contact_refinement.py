"""Evaluate one predeclared contact refinement against its archived baseline."""
import argparse,json,hashlib
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);a=p.parse_args();root=Path(__file__).resolve().parents[3]
plan=json.loads((a.source/'plan.json').read_text());baseline=root/plan['baseline']/'evaluation.json';current=a.source/'contact/evaluation.json';old=json.loads(baseline.read_text());new=json.loads(current.read_text());rows=[]
for name in ('BOOT','YOKE'):
 value=abs(new['max_displacement_mm'][name]/old['max_displacement_mm'][name]-1);limit=plan['criteria']['relative_displacement'];rows.append({'quantity':'displacement','part':name,'relative_change':value,'limit':limit,'passed':value<=limit})
value=abs(new['pressure_max_MPa']/old['pressure_max_MPa']-1);limit=plan['criteria']['relative_peak_pressure'];rows.append({'quantity':'peak_pressure','relative_change':value,'limit':limit,'passed':value<=limit})
r={'comparisons':rows,'source_sha256':{str(f.resolve().relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in (baseline,current)},'numerical_gates_pass':all(x['passed'] for x in rows) and new['local_numerical_probe_pass'],'joint_verified':False}
(a.source/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
