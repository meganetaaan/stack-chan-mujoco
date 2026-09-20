"""Evaluate force balance and overclosure of the local boot seat contact probe."""
import argparse,json,re
from pathlib import Path
import numpy as np
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);a=p.parse_args()
plan=json.loads((a.source/'plan.json').read_text());run=json.loads((a.source/'run.json').read_text());text=(a.source/'contact.dat').read_text()
forces={}
for name,t,values in re.findall(r'total force \(fx,fy,fz\) for set (SUPPORT|ANCHORS) and time\s+(\S+)\s*\n\s*\n([^\n]+)',text):
 if float(t)==1:forces[name]=np.array([float(x) for x in values.split()])
blocks={}
for key in ('relative contact displacement','contact stress'):
 for t,values in re.findall(re.escape(key)+r'.*? time\s+(\S+)\s*\n\s*\n(.*?)(?=\n\s*\n)',text,re.S):
  if float(t)==1:blocks[key]=np.array([[float(x) for x in row.split()[2:]] for row in values.splitlines() if row.strip()])
if set(forces)!= {'SUPPORT','ANCHORS'} or len(blocks)!=2:raise ValueError('missing final data')
gap=blocks['relative contact displacement'][:,0];pressure=blocks['contact stress'][:,0]
if not all(np.isfinite(v).all() for v in [*forces.values(),gap,pressure]):raise ValueError('nonfinite output')
balance=float(np.linalg.norm(forces['SUPPORT']+forces['ANCHORS']+[0,0,-20])/20);penetration=float(max(0,-gap.min()))
displacements=None
for t,values in re.findall(r'displacements \(vx,vy,vz\) for set SEAT and time\s+(\S+)\s*\n\s*\n(.*?)(?=\n\s*\n)',text,re.S):
 if float(t)==1:displacements=np.array([[float(x) for x in row.split()[1:]] for row in values.splitlines() if row.strip()])
if displacements is None or not np.isfinite(displacements).all():raise ValueError('missing finite displacement')
gates={'solver_completion':run['solver_completed'],'force_balance':balance<=plan['criteria']['relative_force_balance'],'penetration':penetration<=plan['criteria']['penetration_mm']}
r={'max_displacement_mm':float(np.linalg.norm(displacements,axis=1).max()),'final_time':1,'reaction_N':{k:v.tolist() for k,v in forces.items()},'relative_force_balance':balance,'gap_min_mm':float(gap.min()),'gap_max_mm':float(gap.max()),'maximum_penetration_mm':penetration,'pressure_min_MPa':float(pressure.min()),'pressure_max_MPa':float(pressure.max()),'gates':gates,'local_contact_probe_pass':all(gates.values()),'joint_strength_verified':False}
(a.source/'evaluation.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
