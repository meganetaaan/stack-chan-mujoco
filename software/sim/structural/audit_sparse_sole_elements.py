"""Locate all-point stress peaks and inspect tet geometry without excluding peaks."""
import argparse,json,itertools
from pathlib import Path
import numpy as np,meshio
from skfem.io import from_meshio
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path);p.add_argument('--mesh-dir',type=Path);p.add_argument('--mesh-mm');p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False);rows=[]
cases=[('0.7','validation/sole_sparse_mean_v1','validation/sole_fixed_anchors_v1/mesh07'),('0.5','validation/sole_sparse_refine_v1/h05','validation/sole_fixed_anchors_v1/mesh05')]
if any([a.source,a.mesh_dir,a.mesh_mm]):
 if not all([a.source,a.mesh_dir,a.mesh_mm]):p.error('source, mesh-dir and mesh-mm required together')
 cases=[(a.mesh_mm,a.source,a.mesh_dir)]
for h,folder,meshdir in cases:
 fields=np.load(Path(folder)/'fields.npz')
 for part in ['boss','spacer']:
  mesh=from_meshio(meshio.read(Path(meshdir)/part/f'{part}_{h}.msh'));x=mesh.p[:,mesh.t].transpose(2,1,0);vol=abs(np.linalg.det(x[:,1:]-x[:,:1]))/6;edge2=sum(np.sum((x[:,i]-x[:,j])**2,axis=1) for i,j in itertools.combinations(range(4),2));quality=12*(3*vol)**(2/3)/edge2
  stress=fields[part+'_stress_MPa'];eig=np.linalg.eigvalsh(np.moveaxis(stress,(0,1),(-2,-1)));peaks=abs(eig).max(axis=(1,2));assert len(peaks)==len(x);i=int(peaks.argmax());center=x[i].mean(axis=0)
  faces=[(0,1,2),(0,1,3),(0,2,3),(1,2,3)];area=np.array([np.linalg.norm(np.cross(x[i,j]-x[i,k],x[i,l]-x[i,k]))/2 for j,k,l in faces]);alt=3*vol[i]/area
  rows.append({'mesh_mm':float(h),'part':part,'peak_element_index_zero_based':i,'peak_absolute_principal_MPa':float(peaks[i]),'peak_centroid_mm':center.tolist(),'peak_vertices_mm':x[i].tolist(),'peak_volume_mm3':float(vol[i]),'peak_mean_ratio_quality':float(quality[i]),'minimum_mesh_mean_ratio_quality':float(quality.min()),'peak_minimum_altitude_mm':float(alt.min()),'peak_radial_centroid_mm':float(np.linalg.norm(center[:2]-[35,6])),'quality_definition':'12*(3V)^(2/3)/sum(edge_length^2); regular tetrahedron=1; no acceptance threshold or peak exclusion','joint_verified':False})
(a.out/'report.json').write_text(json.dumps({'rows':rows},indent=2)+'\n');print(json.dumps({'rows':[{k:v for k,v in row.items() if k!='peak_vertices_mm'} for row in rows]},indent=2))
