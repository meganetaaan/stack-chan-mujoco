"""Compare full-volume elastic energy and verify saved force/displacement work identity."""
from pathlib import Path
import json,hashlib,argparse
import numpy as np,meshio
cases=[('0.5','validation/sole_rounded_contact_v1','validation/sole_rounded_local_mesh_v1'),('0.35','validation/sole_rounded_refine_v1/analysis','validation/sole_rounded_refine_v1/mesh'),('0.25','validation/sole_rounded_third_mesh_v1/analysis','validation/sole_rounded_third_mesh_v1/mesh')]
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source',type=Path,default=Path('validation/sole_rounded_energy_audit_v1'));args=parser.parse_args()
p=args.source;plan=json.loads((p/'plan.json').read_text());rows=[];hashes={}
if 'cases' in plan: cases=[(c['mesh_mm'],c['analysis'],c['mesh']) for c in plan['cases']]
assert len(cases)>=2, 'At least two cases required'
for h,folder,meshdir in cases:
 f=Path(folder)/'fields.npz';d=np.load(f);hashes[str(f)]=hashlib.sha256(f.read_bytes()).hexdigest();offset=0
 for part,E,nu,patch,sign in [('boss',1120,.35,'nut_bearing',-1),('spacer',193000,.3,'head_bearing',1)]:
  path=Path(meshdir)/part/f'{part}_{h}.msh';m=meshio.read(path);x=m.points[m.cells_dict['tetra']];volume=abs(np.linalg.det(x[:,1:]-x[:,:1]))/6;s=d[part+'_stress_MPa'];density=.5*((1+nu)/E*np.einsum('ijeq,ijeq->eq',s,s)-nu/E*np.einsum('iieq->eq',s)**2);assert np.allclose(density,density[:,:1],rtol=1e-10,atol=1e-14);energy=float(volume@density.mean(axis=1));n=len(m.points);u=d['u_mm'][offset:offset+3*n];w=np.zeros(n)
  triangles=m.cells_dict['triangle'][m.cell_data_dict['gmsh:physical']['triangle']==m.field_data[patch][0]];q=m.points[triangles];areas=np.linalg.norm(np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]),axis=1)/2
  for j in range(3):np.add.at(w,triangles[:,j],areas/3)
  F=np.zeros(3*n);F[2::3]=sign*20*w/w.sum();fc=d['contact_force_N'][offset:offset+3*n];fg=d['gauge_force_N'][offset:offset+3*n];work=float(u@(F+fc+fg));error=abs(2*energy-work)
  rows.append({'mesh_mm':h,'part':part,'volume_mm3':float(volume.sum()),'elastic_energy_Nmm':energy,'external_work_Nmm':float(u@F),'contact_work_Nmm':float(u@fc),'gauge_work_Nmm':float(u@fg),'absolute_identity_error_Nmm':error,'identity_gate':error<=plan['criteria']['absolute_work_identity_error_Nmm']});offset+=3*n
 assert offset==len(d['u_mm'])
changes={part:[abs([r for r in rows if r['part']==part][i]['elastic_energy_Nmm']/[r for r in rows if r['part']==part][i-1]['elastic_energy_Nmm']-1) for i in range(1,len(cases))] for part in ['boss','spacer']}
result={'rows':rows,'successive_relative_energy_changes':changes,'source_sha256':hashes,'joint_verified':False};(p/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
