"""Small-strain P1 frictionless contact with lumped penalty and mean-mode multipliers."""
import argparse,json,hashlib,time
from pathlib import Path
import numpy as np,meshio
from scipy.sparse import block_diag,bmat,csr_matrix,diags
from unilateral_contact import solve
from skfem import Basis,ElementVector,ElementTetP1,asm
from skfem.io import from_meshio
from skfem.models.elasticity import linear_elasticity,lame_parameters
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--penalty',type=float,default=1e6);p.add_argument('--mesh-dir',type=Path,required=True);p.add_argument('--mesh-mm',default='0.7');p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
plan={'scope':__doc__,'force_N':20,'penalty_N_mm3':a.penalty,'max_iterations':80,'criteria':{'equilibrium_residual_N':1e-7,'constraint_residual':1e-8,'maximum_penetration_mm':.01,'relative_gauge_force_sum':1e-4},'limitations':['Small strain, initial normals, node-lumped matching contact; different formulation from CalculiX surface contact.','Isotropic assumed material E=1120/193000 MPa, nu=.35/.3; not certified.','Local preload only, no creep, friction or walking loads.']};(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
Ks=[];Cs=[];Fs=[];parts=[];offset=0
for name,E,nu,patch,loadpatch,sign in [('boss',1120,.35,'spacer_contact','nut_bearing',-1),('spacer',193000,.3,'boss_contact','head_bearing',1)]:
 path=a.mesh_dir/name/f'{name}_{a.mesh_mm}.msh';mesh=from_meshio(meshio.read(path));basis=Basis(mesh,ElementVector(ElementTetP1()));xyz=basis.doflocs[:,::3].T;assert np.allclose(xyz,mesh.p.T)
 lam,mu=lame_parameters(E,nu);K=asm(linear_elasticity(lam,mu),basis);tet=mesh.t.T;x=xyz[tet];vol=abs(np.linalg.det(x[:,1:]-x[:,:1]))/6;weights=np.zeros(len(xyz))
 for j in range(4):np.add.at(weights,tet[:,j],vol/4)
 weights/=weights.sum();r=xyz-weights@xyz;R=np.zeros((len(xyz),3,6));R[:,:,:3]=np.eye(3)
 for i,(rx,ry,rz) in enumerate(r):R[i,:,3:]=[[0,rz,-ry],[-rz,0,rx],[ry,-rx,0]]
 modes=[0,1,5] if name=='boss' else list(range(6));C=(R.reshape(-1,6).T*np.repeat(weights,3))[modes];assert np.linalg.matrix_rank(C@R.reshape(-1,6)[:,modes])==len(modes)
 def surface_weights(label):
  tri=mesh.facets[:,mesh.boundaries[label]].T;y=xyz[tri];areas=np.linalg.norm(np.cross(y[:,1]-y[:,0],y[:,2]-y[:,0]),axis=1)/2;w=np.zeros(len(xyz))
  for j in range(3):np.add.at(w,tri[:,j],areas/3)
  return w
 loadw=surface_weights(loadpatch);F=np.zeros(basis.N);F[2::3]=sign*20*loadw/loadw.sum();contactw=surface_weights(patch)
 parts.append({'name':name,'basis':basis,'xyz':xyz,'lam':lam,'mu':mu,'contactw':contactw,'offset':offset,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()});Ks.append(K);Cs.append(csr_matrix(C));Fs.append(F);offset+=basis.N
K=block_diag(Ks,format='csr');C=block_diag(Cs,format='csr');F=np.concatenate(Fs);boss,spacer=parts
ids=np.flatnonzero(boss['contactw']);lookup={tuple(np.round(spacer['xyz'][i],9)):i for i in np.flatnonzero(spacer['contactw'])};other=np.array([lookup[tuple(np.round(boss['xyz'][i],9))] for i in ids]);assert np.allclose(boss['contactw'][ids],spacer['contactw'][other],rtol=1e-8,atol=1e-10)
n=len(ids);B=csr_matrix((np.r_[np.ones(n),-np.ones(n)],(np.r_[np.arange(n),np.arange(n)],np.r_[3*ids+2,spacer['offset']+3*other+2])),shape=(n,len(F)));area=boss['contactw'][ids];active=np.ones(n,dtype=bool);history=[];start=time.monotonic();converged=False
solution=solve(K,C,F,B,area,plan['penalty_N_mm3'],max_iterations=plan['max_iterations']);u=solution['u'];multipliers=solution['multipliers'];gap=solution['gap'];history=solution['history'];converged=solution['converged'];A=solution['matrix']
pressure=np.maximum(-plan['penalty_N_mm3']*gap,0);contact_force=B.T@(area*pressure);gauge_force=-C.T@multipliers;residual=K@u-F-contact_force-gauge_force;results={};arrays={'u_mm':u,'pressure_MPa':pressure,'gap_mm':gap,'contact_area_mm2':area,'gauge_force_N':gauge_force,'multipliers':multipliers,'contact_coordinates_mm':boss['xyz'][ids]}
for item,Kp in zip(parts,Ks):
 o=item['offset'];basis=item['basis'];up=u[o:o+basis.N];g=basis.interpolate(up).grad;strain=(g+g.swapaxes(0,1))/2;stress=2*item['mu']*strain+item['lam']*np.einsum('iieq->eq',strain)[None,None]*np.eye(3)[:,:,None,None];eig=np.linalg.eigvalsh(np.moveaxis(stress,(0,1),(-2,-1)));results[item['name']]={'max_displacement_mm':float(np.linalg.norm(up.reshape(-1,3),axis=1).max()),'max_absolute_principal_MPa':float(abs(eig).max())};arrays[item['name']+'_stress_MPa']=stress
ratio=float(np.linalg.norm(gauge_force.reshape(-1,3),axis=1).sum()/20);eq=float(np.linalg.norm(residual));cr=float(abs(C@u).max());penetration=float(max(0,-gap.min()));r={'converged_active_set':converged,'iterations':history,'elapsed_seconds':time.monotonic()-start,'matrix_dofs':A.shape[0],'matrix_nonzeros':A.nnz,'equilibrium_residual_N':eq,'mean_constraint_residual':cr,'gauge_force_sum_relative':ratio,'contact_total_N':float(area@pressure),'maximum_penetration_mm':penetration,'maximum_pressure_MPa':float(pressure.max()),'parts':results,'gates':{'active_set':converged,'equilibrium':eq<=1e-7,'mean_constraints':cr<=1e-8,'penetration':penetration<=.01,'gauge_force':ratio<=1e-4},'joint_verified':False,'source_sha256':{x['name']:x['sha256'] for x in parts}};(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');np.savez_compressed(a.out/'fields.npz',**arrays);print(json.dumps(r,indent=2))
