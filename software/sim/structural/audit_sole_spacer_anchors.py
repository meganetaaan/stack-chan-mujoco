"""Audit each anchor force and moment, without cancellation credit."""
import argparse, gzip, json, re
from pathlib import Path
import numpy as np
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);a=p.parse_args()
plan=json.loads((a.source/'anchor_plan.json').read_text());assembly=json.loads((a.source/'assembly.json').read_text())
f=a.source/'contact.dat';text=f.read_text() if f.exists() else gzip.open(str(f)+'.gz','rt').read()
blocks=re.findall(r'forces \(fx,fy,fz\) for set ANCHORS and time\s+(\S+)\s*\n\s*\n(.*?)(?=\n\s*\n)',text,re.S)
rows=None
for t,body in blocks:
 if abs(float(t)-1)<1e-10:
  rows=[]
  for line in body.splitlines():
   values=line.split();node=str(int(values[0]));force=np.array(list(map(float,values[1:4])));xyz=np.array(assembly['anchors'][node]);moment=np.cross(xyz-plan['moment_origin_mm'],force)
   rows.append({'node':int(node),'position_mm':xyz.tolist(),'force_N':force.tolist(),'moment_Nmm':moment.tolist()})
if rows is None or {str(r['node']) for r in rows}!=set(assembly['anchors']):raise ValueError('Missing or mismatched individual anchor fields')
f=np.array([r['force_N'] for r in rows]);m=np.array([r['moment_Nmm'] for r in rows]);assert np.isfinite(f).all() and np.isfinite(m).all()
f_ratio=float(np.linalg.norm(f,axis=1).sum()/plan['reference_force_N']);m_ratio=float(np.linalg.norm(m,axis=1).sum()/(plan['reference_force_N']*plan['reference_length_mm']))
r={'rows':rows,'sum_force_norms_relative':f_ratio,'sum_moment_norms_relative':m_ratio,'resultant_force_N':f.sum(axis=0).tolist(),'resultant_moment_Nmm':m.sum(axis=0).tolist(),'gates':{'individual_force_budget':f_ratio<=plan['maximum_sum_force_norms_ratio'],'individual_moment_budget':m_ratio<=plan['maximum_sum_moment_norms_ratio']},'joint_verified':False}
(a.source/'anchor_evaluation.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
