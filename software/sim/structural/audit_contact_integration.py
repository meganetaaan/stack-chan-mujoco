"""Reintegrate pressure over clipped active polygons of a stored P1 gap field."""
import argparse,json
from pathlib import Path
import numpy as np,meshio
from skfem.io import from_meshio
from bound_projected_contact_gap import clip,area,bary
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
plan={'scope':__doc__,'relative_force_error_max':.01,'penalty_N_mm3':1e6,'limitations':['Postprocesses fixed displacement; not a new equilibrium solution.','Affine initial-normal P1 gap only; numerical polygon clipping.']};(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
root=Path('validation/sole_extended_contact_mesh_v1');b,s=[from_meshio(meshio.read(root/n/f'{n}_0.5.msh')) for n in ['boss','spacer']];bx=b.p.T;sx=s.p.T
bt=b.facets[:,np.r_[b.boundaries['spacer_contact'],b.boundaries['contact_extension']]].T;flat=s.boundaries['boss_contact'];st=s.facets[:,np.r_[flat,s.boundaries['contact_extension']]].T;master=bx[bt];lower=master[:,:,:2].min(axis=1);upper=master[:,:,:2].max(axis=1)
f=np.load('validation/sole_projected_contact_probe_v1/fields.npz');u=f['u_mm'];bu=u[:3*len(bx)].reshape(-1,3);su=u[3*len(bx):].reshape(-1,3);total=0.;active_area=0.;extension_area=0.;extension_force=0.;maxp=0.;pieces=0
for i,ids in enumerate(st):
 tri=sx[ids];lo=tri[:,:2].min(axis=0);hi=tri[:,:2].max(axis=0);candidates=np.flatnonzero(np.all(upper>=lo-1e-10,axis=1)&np.all(lower<=hi+1e-10,axis=1))
 for j in candidates:
  poly=clip(list(tri[:,:2]),master[j,:,:2])
  if area(poly)<1e-14:continue
  def gap(q):return float(bary(q,master[j])@(master[j,:,2]+bu[bt[j],2])-bary(q,tri)@(tri[:,2]+su[ids,2]))
  # Clip the affine gap at zero; negative gap is the penalized active region.
  active=[];prev=poly[-1];gp=gap(prev)
  for cur in poly:
   gc=gap(cur)
   if (gp<0)!=(gc<0):active.append(prev+(cur-prev)*(gp/(gp-gc)))
   if gc<0:active.append(cur)
   prev=cur;gp=gc
  if area(active)<1e-18:continue
  pieces+=1
  for k in range(1,len(active)-1):
   t=[active[0],active[k],active[k+1]];ar=area(t);press=np.maximum(-plan['penalty_N_mm3']*np.array([gap(q) for q in t]),0);force=ar*press.mean();total+=force;active_area+=ar;maxp=max(maxp,float(press.max()))
   if i>=len(flat):extension_area+=ar;extension_force+=force
sampled=float(f['contact_area_mm2']@f['pressure_MPa']);error=abs(total-sampled)/abs(sampled)
r={'active_overlap_polygons':pieces,'clipped_projected_contact_area_mm2':active_area,'clipped_pressure_integral_N':total,'solver_quadrature_integral_N':sampled,'relative_force_error':error,'force_integration_gate':bool(error<=.01),'extension_contact_projected_area_mm2':extension_area,'extension_contact_force_N':extension_force,'maximum_affine_pressure_MPa':maxp,'joint_verified':False};(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
