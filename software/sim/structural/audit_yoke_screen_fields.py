"""Locate full-yoke peaks and audit applied quadrature traction, not nodal signs."""
import argparse,json
from pathlib import Path
import numpy as np,meshio
from skfem import FacetBasis,ElementVector,ElementTetP2
from skfem.io import from_meshio
from elasticity import skew,select_boundary
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);a=p.parse_args();plan=json.loads((a.source/'plan.json').read_text())
with np.load(a.source/'fields.npz') as d:
 u=d['displacement_mm'];xyz=d['nodes_mm'];i=int(np.linalg.norm(u,axis=1).argmax());disp={'coordinates_mm':xyz[i].tolist(),'vector_mm':u[i].tolist()}
 stress=np.moveaxis(d['stress_MPa'],(0,1),(-2,-1));peak=abs(np.linalg.eigvalsh(stress)).max(axis=-1);j=np.unravel_index(peak.argmax(),peak.shape);stresspeak={'coordinates_mm':d['quadrature_coordinates_mm'][:,j[0],j[1]].tolist(),'absolute_principal_MPa':float(peak[j])}
mesh=from_meshio(meshio.read(a.source/'yoke.msh'));face=FacetBasis(mesh,ElementVector(ElementTetP2()),facets=select_boundary(mesh,lambda x:abs(x[2]+19)<1e-6));coords=face.global_coordinates();origin=np.array(plan['origin_mm']);mat=np.zeros((6,6))
for f in range(coords.shape[1]):
 for q in range(coords.shape[2]):
  r=coords[:,f,q]-origin;mat+=np.vstack((np.eye(3),skew(r)))@np.hstack((np.eye(3),-skew(r)))*face.dx[f,q]
c=np.linalg.solve(mat,plan['wrench_N_Nmm']);t=c[:3,None,None]+np.cross(c[3:],np.moveaxis(coords-origin[:,None,None],0,-1)).transpose(2,0,1)
force=(t*face.dx).sum(axis=(1,2));moment=(np.cross(np.moveaxis(coords-origin[:,None,None],0,-1),np.moveaxis(t,0,-1))*face.dx[...,None]).sum(axis=(0,1));assert np.allclose(np.r_[force,moment],plan['wrench_N_Nmm'],atol=1e-7)
r={'peak_displacement':disp,'peak_stress':stresspeak,'traction_z_min_MPa':float(t[2].min()),'traction_z_max_MPa':float(t[2].max()),'negative_z_area_fraction':float(face.dx[t[2]<0].sum()/face.dx.sum()),'negative_z_force_N':float((np.minimum(t[2],0)*face.dx).sum()),'positive_z_force_N':float((np.maximum(t[2],0)*face.dx).sum()),'nonadhesive_normal_contact_compatible':bool(t[2].min()>=-1e-12),'joint_verified':False};(a.source/'field_audit.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
