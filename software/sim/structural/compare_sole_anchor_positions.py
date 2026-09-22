"""Compare fixed-mesh anchor cases after removing per-part infinitesimal rigid motion."""
import argparse,gzip,json,re
from pathlib import Path
import numpy as np
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--baseline',type=Path,required=True);p.add_argument('--variant',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
plan=json.loads((a.out/'comparison_plan.json').read_text())
def read_case(folder):
 f=folder/'contact.dat';text=f.read_text() if f.exists() else gzip.open(str(f)+'.gz','rt').read()
 xyz={};active=False
 for line in (folder/'contact.inp').read_text().splitlines():
  if line.startswith('*'):active=line.upper().startswith('*NODE,');continue
  if active:
   vals=line.split(',');xyz[int(vals[0])]=list(map(float,vals[1:4]))
 out={}
 for name,t,body in re.findall(r'displacements \(vx,vy,vz\) for set (BOSS|SPACER) and time\s+(\S+)\s*\n\s*\n(.*?)(?=\n\s*\n)',text,re.S):
  if float(t)!=1:continue
  data=np.array([list(map(float,line.split())) for line in body.splitlines() if line.strip()]);pos=np.array([xyz[int(i)] for i in data[:,0]]);r=pos-pos.mean(axis=0);u=data[:,1:4];B=np.zeros((len(r),3,6));B[:,:,:3]=np.eye(3)
  for i,(x,y,z) in enumerate(r): B[i,:,3:]=[[0,z,-y],[-z,0,x],[y,-x,0]]
  coef=np.linalg.lstsq(B.reshape(-1,6),u.reshape(-1),rcond=None)[0];res=u-(B@coef)
  out[name]={'max_nonrigid_displacement_mm':float(np.linalg.norm(res,axis=1).max()),'rms_nonrigid_displacement_mm':float(np.sqrt(np.mean(res**2)))}
 assert set(out)=={'BOSS','SPACER'}
 out['pressure_max_MPa']=json.loads((folder/'evaluation.json').read_text())['pressure_max_MPa']
 return out
b=read_case(a.baseline);v=read_case(a.variant)
changes={name:abs(v[name]['max_nonrigid_displacement_mm']/b[name]['max_nonrigid_displacement_mm']-1) for name in ['BOSS','SPACER']}
pc=abs(v['pressure_max_MPa']/b['pressure_max_MPa']-1)
r={'baseline':b,'opposite':v,'relative_nonrigid_peak_change':changes,'relative_pressure_peak_change':pc,'gates':{'nonrigid_displacement_sensitivity':all(c<=plan['displacement_relative_change_max'] for c in changes.values()),'pressure_sensitivity':pc<=plan['pressure_relative_change_max']},'joint_verified':False,'limitation':'Per-part least-squares small-rotation fit is a diagnostic; not a pointwise strain or full rigid-rotation invariant finite-strain comparison.'}
(a.out/'comparison.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
