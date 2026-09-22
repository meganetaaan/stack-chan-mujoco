"""Locate faces containing peak contact samples; DAT does not supply sample coordinates."""
import argparse,json,re,hashlib
from pathlib import Path
import meshio,numpy as np
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();root=Path(__file__).resolve().parents[3]
if a.out.exists():p.error('new output required')
a.out.mkdir(parents=True)
folders={1:root/'validation/boot_yoke_mesh_sensitivity_v1/h1',.7:root/'validation/boot_yoke_deformable_contact_v1',.5:root/'validation/boot_yoke_mesh_sensitivity_v1/h0.5'}
faces=[(0,1,2),(0,3,1),(1,3,2),(2,3,0)];rows=[];hashes={}
for size,folder in folders.items():
 dat=folder/'contact.dat';meshpath=root/f'validation/boot_nut_patch_development_v1/seat_{size}.msh';hashes[str(dat.relative_to(root))]=hashlib.sha256(dat.read_bytes()).hexdigest();hashes[str(meshpath.relative_to(root))]=hashlib.sha256(meshpath.read_bytes()).hexdigest()
 values=None
 for t,s in re.findall(r'contact stress .*? time\s+(\S+)\s*\n\s*\n(.*?)(?=\n\s*\n)',dat.read_text(),re.S):
  if float(t)==1:values=np.array([[float(v) for v in line.split()] for line in s.splitlines() if line.strip()])
 if values is None or not np.isfinite(values).all():raise ValueError('missing pressure samples')
 peak=values[np.argmax(values[:,2])];eid,face=int(peak[0]),int(peak[1]);m=meshio.read(meshpath);triangle=m.points[m.cells_dict['tetra'][eid-1][list(faces[face-1])]]
 radii=np.linalg.norm(triangle[:,:2]-[-34,-14.5],axis=1)
 rows.append({'mesh_mm':size,'peak_pressure_MPa':float(peak[2]),'slave_element':eid,'face':face,'triangle_vertices_reference_mm':triangle.tolist(),'triangle_centroid_reference_mm':triangle.mean(axis=0).tolist(),'vertex_radius_about_hole_mm':radii.tolist(),'face_touches_outer_radius_3mm':bool(np.any(abs(radii-3)<1e-5)),'face_touches_hole_radius_1_15mm':bool(np.any(abs(radii-1.15)<1e-5)),'sample_coordinate_known':False})
report={'rows':rows,'source_sha256':hashes,'limitations':['Triangle location only, not actual contact integration-point location.','A peak on an edge face does not by itself prove a mathematical singularity.','No stress values excluded or acceptance criterion changed.']}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(rows,indent=2))
