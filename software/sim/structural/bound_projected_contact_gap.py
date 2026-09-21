"""Bound linearized vertical gap over intersections of master/slave P1 triangles."""
import argparse,json
from pathlib import Path
import numpy as np,meshio
from skfem.io import from_meshio

def cross(a,b):return a[0]*b[1]-a[1]*b[0]
def area(poly):
 if len(poly)<3:return 0.
 q=np.asarray(poly)-poly[0];return abs(sum(cross(q[i],q[(i+1)%len(q)]) for i in range(len(q))))/2

def clip(poly,tri):
 if cross(tri[1]-tri[0],tri[2]-tri[0])<0:tri=tri[[0,2,1]]
 for k in range(3):
  if not len(poly):break
  a,b=tri[k],tri[(k+1)%3];out=[];prev=poly[-1];dp=cross(b-a,prev-a)
  for cur in poly:
   dc=cross(b-a,cur-a);ip=dp>=-1e-12;ic=dc>=-1e-12
   if ip!=ic:
    denom=dp-dc
    if abs(denom)>1e-20:out.append(prev+(cur-prev)*(dp/denom))
   if ic:out.append(cur)
   prev=cur;dp=dc
  poly=out
 return poly

def bary(q,tri):
 uv=np.linalg.solve((tri[1:,:2]-tri[0,:2]).T,np.asarray(q)-tri[0,:2]);return np.r_[1-uv.sum(),uv]

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    plan={'scope':__doc__,'relative_area_coverage_tolerance':1e-8,'maximum_penetration_mm':.01,'assumptions':['P1 displacement on initial planar triangles, vertical projection and small-displacement gap.','Finite rotation, curved CAD between facets and actual surface roughness excluded.'],'clipping_halfplane_tolerance_mm2':1e-12};(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    root=Path('validation/sole_extended_contact_mesh_v1');b,s=[from_meshio(meshio.read(root/n/f'{n}_0.5.msh')) for n in ['boss','spacer']];bx=b.p.T;sx=s.p.T
    bt=b.facets[:,np.r_[b.boundaries['spacer_contact'],b.boundaries['contact_extension']]].T;st=s.facets[:,np.r_[s.boundaries['boss_contact'],s.boundaries['contact_extension']]].T;master=bx[bt];lower=master[:,:,:2].min(axis=1);upper=master[:,:,:2].max(axis=1);u=np.load('validation/sole_projected_contact_probe_v1/fields.npz')['u_mm'];bu=u[:3*len(bx)].reshape(-1,3);su=u[3*len(bx):].reshape(-1,3)
    minimum=float('inf');peak=None;coverage=[];pieces=0
    for i,ids in enumerate(st):
     tri=sx[ids];lo=tri[:,:2].min(axis=0);hi=tri[:,:2].max(axis=0);candidates=np.flatnonzero(np.all(upper>=lo-1e-10,axis=1)&np.all(lower<=hi+1e-10,axis=1));covered=0.;expected=area(list(tri[:,:2]))
     for j in candidates:
      poly=clip(list(tri[:,:2]),master[j,:,:2]);ar=area(poly)
      if ar<1e-14:continue
      covered+=ar;pieces+=1
      for q in poly:
       sw=bary(q,tri);bw=bary(q,master[j]);gap=bw@(master[j,:,2]+bu[bt[j],2])-sw@(tri[:,2]+su[ids,2])
       if gap<minimum:minimum=float(gap);peak={'xy_mm':np.asarray(q).tolist(),'slave_triangle_index':i,'master_triangle_index':int(j)}
     coverage.append(abs(covered-expected)/expected)
    r={'overlap_polygons':pieces,'maximum_relative_triangle_area_coverage_error':max(coverage),'coverage_gate':bool(max(coverage)<=1e-8),'minimum_linearized_vertical_gap_mm':minimum,'peak':peak,'penetration_gate':minimum>=-.01,'bound_scope':'Affine gap minimum at polygon vertices; numerical clipping coverage checked, not interval-arithmetic proof','joint_verified':False};(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
