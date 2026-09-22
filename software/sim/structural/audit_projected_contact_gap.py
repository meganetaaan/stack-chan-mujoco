"""Resample stored displacement at contact vertices and edge midpoints."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np,meshio
from skfem.io import from_meshio
from project_sole_contact import project
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
source=Path('validation/sole_projected_contact_probe_v1/fields.npz');meshdir=Path('validation/sole_extended_contact_mesh_v1')
plan={'scope':__doc__,'maximum_penetration_mm':.01,'limitations':['Finite sample audit only; does not bound gap throughout triangles crossing master edges.','Initial vertical projection, small-displacement model.'],'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest()};(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
meshes=[from_meshio(meshio.read(meshdir/n/f'{n}_0.5.msh')) for n in ['boss','spacer']];samples=np.array([[1,0,0],[0,1,0],[0,0,1],[.5,.5,0],[0,.5,.5],[.5,0,.5]])
B,area,gap0,x,projection=project(*meshes,sample_barycentric=samples);f=np.load(source);gap=gap0+B@f['u_mm'];i=int(gap.argmin());unique=np.unique(np.round(np.c_[x,gap0,gap],12),axis=0);flat=gap0<1e-8
r={'samples_with_triangle_duplicates':len(gap),'unique_samples':len(unique),'minimum_gap_mm':float(gap[i]),'minimum_gap_position_mm':x[i].tolist(),'maximum_penetration_mm':float(max(0,-gap.min())),'solver_quadrature_maximum_penetration_mm':float(max(0,-f['gap_mm'].min())),'initially_gapped_samples_penetrating':int(np.sum((~flat)&(gap<0))),'penetration_gate':bool(gap.min()>=-plan['maximum_penetration_mm']),'continuous_nonpenetration_verified':False,'joint_verified':False}
np.savez_compressed(a.out/'samples.npz',coordinates_mm=x,initial_gap_mm=gap0,final_gap_mm=gap);(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
