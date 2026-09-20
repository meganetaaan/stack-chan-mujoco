"""Evaluate final equilibrium and overclosure for the deformable local joint."""
import argparse,json,re,gzip
from pathlib import Path
import numpy as np
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);a=p.parse_args();dat=a.source/'contact.dat';text=dat.read_text() if dat.exists() else gzip.open(a.source/'contact.dat.gz','rt').read();plan=json.loads((a.source/'plan.json').read_text());run=json.loads((a.source/'run.json').read_text())
reaction=None;fields={};displacements={}
for t,values in re.findall(r'total force \(fx,fy,fz\) for set ANCHORS and time\s+(\S+)\s*\n\s*\n([^\n]+)',text):
 if float(t)==1:reaction=np.array([float(x) for x in values.split()])
for key in ('relative contact displacement','contact stress'):
 for t,values in re.findall(re.escape(key)+r'.*? time\s+(\S+)\s*\n\s*\n(.*?)(?=\n\s*\n)',text,re.S):
  if float(t)==1:fields[key]=np.array([[float(x) for x in row.split()[2:]] for row in values.splitlines() if row.strip()])
for name,t,values in re.findall(r'displacements \(vx,vy,vz\) for set (BOOT|YOKE) and time\s+(\S+)\s*\n\s*\n(.*?)(?=\n\s*\n)',text,re.S):
 if float(t)==1:displacements[name]=np.array([[float(x) for x in row.split()[1:]] for row in values.splitlines() if row.strip()])
if reaction is None or len(fields)!=2 or len(displacements)!=2:raise ValueError('missing final fields')
if not all(np.isfinite(x).all() for x in [reaction,*fields.values(),*displacements.values()]):raise ValueError('nonfinite fields')
gap=fields['relative contact displacement'][:,0];pressure=fields['contact stress'][:,0];ratio=float(np.linalg.norm(reaction)/20);penetration=float(max(0,-gap.min()))
gates={'solver_completion':run['solver_completed'],'anchor_force':ratio<=plan['criteria']['relative_anchor_force'],'penetration':penetration<=plan['criteria']['maximum_penetration_mm']}
r={'anchor_resultant_N':reaction.tolist(),'relative_anchor_force':ratio,'gap_min_mm':float(gap.min()),'gap_max_mm':float(gap.max()),'maximum_penetration_mm':penetration,'pressure_min_MPa':float(pressure.min()),'pressure_max_MPa':float(pressure.max()),'max_displacement_mm':{k:float(np.linalg.norm(v,axis=1).max()) for k,v in displacements.items()},'gates':gates,'local_numerical_probe_pass':all(gates.values()),'joint_strength_verified':False}
(a.source/'evaluation.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
