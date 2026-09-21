"""Identify deformation/load-path regions without additional mesh refinement."""
import argparse,hashlib,json
from pathlib import Path
import meshio
import numpy as np
from skfem import Basis,ElementVector,ElementTetP2
from skfem.io import from_meshio
from elasticity import analyze,tetrahedralize
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
source=Path('validation/yaw_shelf_compliance_v1/plan.json');previous=json.loads(source.read_text())
plan={'question':'Is deformation primarily in the rear wall or in the shelf/span, and is plate seat motion mostly rigid?',
 'parent_plan_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
 'stop':'One existing 3 mm mesh and archived load; energy partition and rigid-fit diagnostics only, no stress convergence or qualification.',
 'regions_x_mm':{'rear':[-100,-50],'middle':[-50,-30],'front':[-30,100]},
 'limits':['Region boundaries are diagnostic assumptions, not separate physical components.','Nodal rigid fit uses equal node weighting and is not a contact solution.','Energy partition is quadrature-point based; it is not a strength margin.']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
path=Path('validation/yaw_shelf_compliance_v1/relief_3.msh')
if path.exists(): mesh=from_meshio(meshio.read(path))
else:
 path=a.out/'relief_3.msh';mesh=tetrahedralize('validation/yaw_connector_shelf_relief_v2/left_yaw_fixed_support.step',path,3)
loaded=lambda x:(abs(x[2]-89)<1e-6)&(x[0]>=-37.5)&(x[0]<=11.6)&(x[1]>=9.5)&(x[1]<=42.5)
r,d=analyze(mesh,lambda x:abs(x[0]+62.2)<1e-6,loaded,previous['origin_mm'],previous['source_case']['selected_wrench_N_Nmm'],1120,.35)
basis=Basis(mesh,ElementVector(ElementTetP2()))
s=d['stress_MPa'];trace=np.einsum('iieq->eq',s)
density=(1+.35)/(2*1120)*np.einsum('ijeq,ijeq->eq',s,s)-.35/(2*1120)*trace**2
energy=density*basis.dx;total=float(energy.sum());assert np.isclose(total,r['strain_energy_Nmm'],rtol=1e-8)
regions=[]
xq=d['quadrature_coordinates_mm'][0]
for name,(lo,hi) in plan['regions_x_mm'].items():
 value=float(energy[(xq>=lo)&(xq<hi)].sum());regions.append({'region':name,'energy_Nmm':value,'fraction':value/total})
assert np.isclose(sum(v['energy_Nmm'] for v in regions),total)
nodes=d['nodes_mm'];u=d['displacement_mm'];selected=loaded(nodes.T)
points=nodes[selected];disp=u[selected];origin=points.mean(axis=0);rel=points-origin
A=np.zeros((len(points),3,6));A[:,:,:3]=np.eye(3)
for i,(x,y,z) in enumerate(rel):A[i,:,3:]=[[0,z,-y],[-z,0,x],[y,-x,0]]
fit=np.linalg.lstsq(A.reshape(-1,6),disp.ravel(),rcond=None)[0]
residual=disp-np.einsum('ijk,k->ij',A,fit)
index=int(np.linalg.norm(u,axis=1).argmax())
result={'mesh_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'solver_report':r,'regions':regions,
 'maximum_displacement_location_mm':nodes[index].tolist(),'maximum_displacement_vector_mm':u[index].tolist(),
 'seat_rigid_fit':{'nodes':len(points),'origin_mm':origin.tolist(),'translation_mm':fit[:3].tolist(),'rotation_rad':fit[3:].tolist(),'max_nonrigid_residual_mm':float(np.linalg.norm(residual,axis=1).max()),'rms_nonrigid_residual_mm':float(np.sqrt(np.mean(np.sum(residual**2,axis=1))))},
 'manufacturing_release':False}
(a.out/'report.json').write_text(json.dumps(result,indent=2)+'\n')
np.savez_compressed(a.out/'field.npz',**d)
print(json.dumps(result,indent=2))
