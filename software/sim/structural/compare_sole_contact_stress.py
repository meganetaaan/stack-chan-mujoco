"""Unfiltered integration-point stress sensitivity of boss and spacer contact cases."""
import argparse,gzip,json,re
from pathlib import Path
import numpy as np
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--baseline',type=Path,required=True);p.add_argument('--variant',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
plan=json.loads((a.out/'comparison_plan.json').read_text())
def parse(folder):
 f=folder/'contact.dat';text=f.read_text() if f.exists() else gzip.open(str(f)+'.gz','rt').read();parts={}
 for name,t,rows in re.findall(r'stresses \(elem, integ.pnt.,sxx,syy,szz,sxy,sxz,syz\) for set (BOSS|SPACER) and time\s+(\S+)\s*\n\s*\n(.*?)(?=\n\s*\n)',text,re.S):
  if float(t)!=1:continue
  x=np.array([[float(v) for v in line.split()] for line in rows.splitlines() if line.strip()]);assert x.shape[1]==8 and np.isfinite(x).all()
  s=x[:,2:];m=np.zeros((len(s),3,3));m[:,0,0]=s[:,0];m[:,1,1]=s[:,1];m[:,2,2]=s[:,2];m[:,0,1]=m[:,1,0]=s[:,3];m[:,0,2]=m[:,2,0]=s[:,4];m[:,1,2]=m[:,2,1]=s[:,5]
  eig=np.linalg.eigvalsh(m);peak=np.max(abs(eig),axis=1);i=int(peak.argmax());vm=np.sqrt(((eig[:,0]-eig[:,1])**2+(eig[:,1]-eig[:,2])**2+(eig[:,2]-eig[:,0])**2)/2)
  parts[name]={'absolute_principal_MPa':float(peak[i]),'peak_element':int(x[i,0]),'maximum_von_mises_MPa':float(vm.max()),'integration_points':len(x)}
 assert set(parts)=={'BOSS','SPACER'}
 assert json.loads((folder/'run.json').read_text())['solver_completed']
 return parts
b=parse(a.baseline);v=parse(a.variant);changes={n:abs(v[n]['absolute_principal_MPa']/b[n]['absolute_principal_MPa']-1) for n in b}
r={'baseline':b,'variant':v,'relative_peak_stress_change':changes,'convergence_gates':{n:c<=plan['stress_relative_change_max'] for n,c in changes.items()},'joint_strength_verified':False,'note':'No excluded singularities or averaged nodal stresses. Allowable material stress is not certified here.'}
(a.out/'stress_comparison.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
