"""Frictionless nodal unilateral contact against a rigid nominal rail: diagnostic only."""
import argparse,hashlib,json
from pathlib import Path
import meshio,numpy as np
from scipy.sparse.linalg import splu
from scipy.optimize import minimize
from skfem import Basis,ElementVector,ElementTetP2,asm
from skfem.io import from_meshio
from skfem.models.elasticity import linear_elasticity,lame_parameters
from elasticity import select_boundary
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
fieldpath=Path('validation/yaw_rail_seat_deformation_location_v1/field.npz');meshpath=Path('validation/yaw_rail_seat_deformation_v1/support_3.msh');contacts=Path('validation/yaw_rail_contact_motion_v1/report.json')
plan={'question':'Can a rigid frictionless zero-gap rail materially resolve the archived displacement shortfall without tensile support?', 'assumptions':['Same archived load, E1120MPa nu0.35 and rear clamp','Rigid rail, zero gap, nodal contact on previously sampled footprint','No friction, preload, real body flexibility or manufacturing gaps'], 'stop':'One existing mesh, max500 QP iterations; require nonpenetration and nonnegative reactions; no refinement','checks_before_solve':{'gap_min_mm':-1e-7,'reaction_min_N':-1e-9,'max_complementarity_Nmm':1e-7,'free_residual_N':1e-7},'manufacturing_release':False}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
d=np.load(fieldpath);mesh=from_meshio(meshio.read(meshpath));b=Basis(mesh,ElementVector(ElementTetP2()));assert np.allclose(b.doflocs[:,::3].T,d['nodes_mm'],rtol=0,atol=1e-10)
fixed=b.get_dofs(facets=select_boundary(mesh,lambda x:abs(x[0]+62.2)<1e-6)).all();free=np.setdiff1d(np.arange(b.N),fixed);K=asm(linear_elasticity(*lame_parameters(1120,.35)),b);factor=splu(K[free][:,free].tocsc());load=d['load_N'].ravel();u0=np.zeros(b.N);u0[free]=factor.solve(load[free]);assert np.allclose(u0.reshape(-1,3),d['displacement_mm'],rtol=1e-6,atol=1e-9)
c=np.array([x['node_index']*3+2 for x in json.loads(contacts.read_text())['samples']]);c=np.setdiff1d(c,fixed);positions=np.searchsorted(free,c)
# Compliance columns for unit upward forces; factorization is reused.
rhs=np.zeros((len(free),len(c)));rhs[positions,np.arange(len(c))]=1
H=factor.solve(rhs);C=H[positions,:];assert np.allclose(C,C.T,atol=1e-9);C=(C+C.T)/2;g0=u0[c]
# Scale variables to improve the optimizer's stopping measure.
scale=1/np.sqrt(np.diag(C));A=C*scale[:,None]*scale[None,:];q=g0*scale
result=minimize(lambda x:(.5*x@A@x+q@x,A@x+q),np.zeros(len(c)),jac=True,bounds=[(0,None)]*len(c),method='L-BFGS-B',options={'maxiter':500,'ftol':1e-15,'gtol':1e-12,'maxls':40})
r=result.x*scale;u=u0.copy();u[free]+=H@r;gap=u[c];res=K@u-load;res[c]-=r
checks={'nonpenetration':float(gap.min())>=-1e-7,'nonnegative_reaction':float(r.min())>=-1e-9,'complementarity':float(np.max(abs(r*gap)))<=1e-7,'equilibrium':float(np.linalg.norm(res[free]))<1e-7}
report={'sources_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [fieldpath,meshpath,contacts]},'contact_dofs':len(c),'optimizer_success':bool(result.success),'message':str(result.message),'iterations':int(result.nit),'checks':checks,'min_gap_mm':float(gap.min()),'max_reaction_N':float(r.max()),'sum_rail_reaction_N':float(r.sum()),'max_complementarity_Nmm':float(np.max(abs(r*gap))),'free_residual_N':float(np.linalg.norm(res[free])),'max_displacement_mm':float(np.linalg.norm(u.reshape(-1,3),axis=1).max()),'no_contact_max_displacement_mm':float(np.linalg.norm(u0.reshape(-1,3),axis=1).max()),'manufacturing_release':False,'displacement_requirement_mm':.2}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');np.savez_compressed(a.out/'contact.npz',dofs=c,gaps_mm=gap,reactions_N=r);print(json.dumps(report,indent=2));assert all(checks.values())
