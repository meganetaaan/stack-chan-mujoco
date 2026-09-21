"""Replace point anchors by volume-weighted mean rigid-motion equations."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from scipy.linalg import qr
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
source=a.source/'contact.inp';lines=source.read_text().splitlines();nodes={};parts={};mode='';part=None
for line in lines:
 if line.startswith('*'):
  mode='node' if line.startswith('*NODE,') else 'element' if line.startswith('*ELEMENT,') else ''
  if mode=='element':part=line.split('ELSET=')[1];parts[part]=[]
  continue
 if mode=='node':v=line.split(',');nodes[int(v[0])]=list(map(float,v[1:4]))
 if mode=='element':parts[part].append(list(map(int,line.split(',')[1:])))
plan={'scope':__doc__,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'criteria':{'rigid_mode_rank':{'BOSS':3,'SPACER':6},'equation_identity_error_max':1e-10},'limitations':['Initial-coordinate linear constraints; finite-rotation objectivity not claimed.','Only constraint construction verified; no contact, strength or reaction qualification.','Weights are tetrahedral volume/4, normalized per part.']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');equations=[];reports=[];arrays={}
for name,tets in parts.items():
 ids=np.array(sorted({n for tet in tets for n in tet}));index={n:i for i,n in enumerate(ids)};xyz=np.array([nodes[n] for n in ids]);weights=np.zeros(len(ids))
 for tet in tets:
  loc=np.array([index[n] for n in tet]);x=xyz[loc];vol=np.linalg.det((x[1:]-x[0]).T)/6
  if vol<=0:raise ValueError('Invalid tet volume')
  weights[loc]+=vol/4
 weights/=weights.sum();center=weights@xyz;r=xyz-center;rigid=np.zeros((len(ids),3,6));rigid[:,:,:3]=np.eye(3)
 for i,(x,y,z) in enumerate(r):rigid[i,:,3:]=[[0,z,-y],[-z,0,x],[y,-x,0]]
 R=rigid.reshape(-1,6);selected=[0,1,5] if name=='BOSS' else list(range(6));C=(R.T*np.repeat(weights,3))[selected];rank=int(np.linalg.matrix_rank(C@R[:,selected]));assert rank==len(selected)
 # Row reduction isolates distinct dependent DOFs and avoids cyclic MPC references.
 _,_,piv=qr(C,pivoting=True,mode='economic');dep=piv[:len(selected)];D=np.linalg.solve(C[:,dep],C);err=float(np.max(abs(D[:,dep]-np.eye(len(dep)))));assert err<1e-10
 for i,col in enumerate(dep):
  coeff=D[i].copy();coeff[dep]=0;coeff[col]=1;cols=[int(col)]+[int(j) for j in np.flatnonzero(coeff) if j!=col];equations+=['*EQUATION',str(len(cols))]
  terms=[f'{ids[j//3]},{j%3+1},{coeff[j]:.12e}' for j in cols]
  equations += [','.join(terms[k:k+4]) for k in range(0,len(terms),4)]
 reports.append({'part':name,'nodes':len(ids),'equations':len(dep),'rigid_mode_rank':rank,'pivot_identity_error':err,'dependent_dofs':[[int(ids[j//3]),int(j%3+1)] for j in dep],'volume_centroid_mm':center.tolist()})
 arrays[name+'_node_ids']=ids;arrays[name+'_matrix']=C;arrays[name+'_reduced_matrix']=D
out=[];skip=False
for line in lines:
 if line.startswith('*BOUNDARY'):
  skip=True;out+=equations;continue
 if skip:
  if not line.startswith('*'):continue
  skip=False
 # Remove obsolete RF output at old point anchors; keep nodal U and contact fields.
 if line.startswith('*NODE PRINT,NSET=ANCHORS'):continue
 if line=='RF':continue
 out.append(line)
assert not any(x.startswith('*BOUNDARY') for x in out)
(a.out/'contact.inp').write_text('\n'.join(out)+'\n');np.savez_compressed(a.out/'constraints.npz',**arrays);report={'parts':reports,'constraint_construction_pass':True,'solver_run':False,'joint_verified':False};(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
