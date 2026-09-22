"""Evaluate unaveraged C3D4 integration-point stresses for two preload meshes."""
import argparse,gzip,json,re
from pathlib import Path
import numpy as np
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);a=p.parse_args()
plan=json.loads((a.source/'plan.json').read_text());cases={}
for h in plan['mesh_mm']:
 folder=a.source/f'h{h:g}';f=folder/'contact.dat';text=f.read_text() if f.exists() else gzip.open(str(f)+'.gz','rt').read();parts={}
 for name,t,rows in re.findall(r'stresses \(elem, integ.pnt.,sxx,syy,szz,sxy,sxz,syz\) for set (BOOT|YOKE) and time\s+(\S+)\s*\n\s*\n(.*?)(?=\n\s*\n)',text,re.S):
  if float(t)!=1:continue
  x=np.array([[float(v) for v in line.split()] for line in rows.splitlines() if line.strip()]);assert x.shape[1]==8 and np.isfinite(x).all()
  s=x[:,2:];m=np.zeros((len(s),3,3));m[:,0,0]=s[:,0];m[:,1,1]=s[:,1];m[:,2,2]=s[:,2];m[:,0,1]=m[:,1,0]=s[:,3];m[:,0,2]=m[:,2,0]=s[:,4];m[:,1,2]=m[:,2,1]=s[:,5]
  eig=np.linalg.eigvalsh(m);peak=np.max(abs(eig),axis=1);i=int(peak.argmax());vm=np.sqrt(((eig[:,0]-eig[:,1])**2+(eig[:,1]-eig[:,2])**2+(eig[:,2]-eig[:,0])**2)/2)
  parts[name]={'absolute_principal_MPa':float(peak[i]),'peak_element':int(x[i,0]),'principal_at_peak_MPa':eig[i].tolist(),'maximum_von_mises_MPa':float(vm.max()),'integration_points':len(x),'allowance_pass':bool(peak[i]<=plan['criteria']['maximum_absolute_principal_MPa'])}
 assert set(parts)=={'BOOT','YOKE'};assert json.loads((folder/'run.json').read_text())['solver_completed'];cases[str(h)]=parts
hs=plan['mesh_mm'];assert len(hs)==2
changes={n:abs(cases[str(hs[1])][n]['absolute_principal_MPa']/cases[str(hs[0])][n]['absolute_principal_MPa']-1) for n in ('BOOT','YOKE')}
r={'cases':cases,'relative_peak_stress_change':changes,'stress_convergence_pass':all(v<=plan['criteria']['relative_peak_stress_change'] for v in changes.values()),'allowance_pass':all(v['allowance_pass'] for c in cases.values() for v in c.values()),'joint_strength_verified':False}
(a.source/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
