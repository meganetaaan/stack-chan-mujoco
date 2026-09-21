"""Locate maximum nodal displacement in each saved rounded-contact mesh without dropping peaks."""
from pathlib import Path
import json,hashlib
import numpy as np,meshio
cases=[('0.5','validation/sole_rounded_contact_v1','validation/sole_rounded_local_mesh_v1'),('0.35','validation/sole_rounded_refine_v1/analysis','validation/sole_rounded_refine_v1/mesh'),('0.25','validation/sole_rounded_third_mesh_v1/analysis','validation/sole_rounded_third_mesh_v1/mesh')]
rows=[];hashes={}
for h,analysis,folder in cases:
 f=Path(analysis)/'fields.npz';u=np.load(f)['u_mm'];hashes[str(f)]=hashlib.sha256(f.read_bytes()).hexdigest();offset=0
 for part in ['boss','spacer']:
  path=Path(folder)/part/f'{part}_{h}.msh';mesh=meshio.read(path);n=len(mesh.points);partu=u[offset:offset+3*n].reshape(n,3);offset+=3*n;norm=np.linalg.norm(partu,axis=1);i=int(norm.argmax());q=mesh.points[i];reported=json.loads((Path(analysis)/'report.json').read_text())['parts'][part]['max_displacement_mm'];assert np.isclose(norm[i],reported,rtol=1e-10,atol=1e-12)
  rows.append({'mesh_mm':h,'part':part,'node_index_zero_based':i,'xyz_mm':q.tolist(),'displacement_xyz_mm':partu[i].tolist(),'norm_mm':float(norm[i]),'radial_position_mm':float(np.linalg.norm(q[:2]-[35,6]))})
 assert offset==len(u)
p=Path('validation/sole_rounded_displacement_peaks_v1');(p/'report.json').write_text(json.dumps({'rows':rows,'fields_sha256':hashes,'scope':'Saved nodal maximum location only; no peak exclusion or convergence claim','joint_verified':False},indent=2)+'\n');print(json.dumps(rows,indent=2))
