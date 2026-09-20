"""Compare nut-footprint traction using validated surface groups on the local seat."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np,meshio
from skfem.io import from_meshio
from elasticity import analyze
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[3]
if a.out.exists():p.error('new output required')
a.out.mkdir(parents=True)
source=root/'validation/boot_nut_patch_development_v1'
paths=[source/f'seat_{size}.msh' for size in (1,.7,.5)]
plan={'scope':__doc__,'source_sha256':{str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in paths},'mesh_mm':[1,.7,.5],'load_N':20,'support':'normal_z on pad_bottom, with minimal in-plane anchors','load':'downward resultant on nut_bearing only','young_MPa':1120,'poisson':.35,'criteria':{'displacement_mm':.2,'stress_MPa':5.6,'last_displacement_relative_change':.05,'last_stress_relative_change':.1},'limitations':['Prescribed traction on actual nominal footprint, not a contact solution.','Bilateral support does not allow separation.','Single cropped seat, isotropic unqualified PETG, no creep or full walking loads.']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');rows=[]
for size,path in zip(plan['mesh_mm'],paths):
 mesh=from_meshio(meshio.read(path))
 r,d=analyze(mesh,'pad_bottom','nut_bearing',[-34,-14.5,-14.6],[0,0,-20,0,0,0],1120,.35,support_mode='normal_z')
 r['mesh_mm']=size;rows.append(r);np.savez_compressed(a.out/f'seat_{size}.npz',**d);print(json.dumps(r),flush=True)
r,b=rows[-1],rows[-2]
gates={'displacement':r['max_displacement_mm']<=.2,'stress':max(r['max_von_mises_MPa'],r['max_absolute_principal_MPa'])<=5.6,'displacement_convergence':abs(r['max_displacement_mm']/b['max_displacement_mm']-1)<=.05,'stress_convergence':abs(r['max_absolute_principal_MPa']/b['max_absolute_principal_MPa']-1)<=.1}
(a.out/'report.json').write_text(json.dumps({'rows':rows,'gates':gates,'local_screen_pass':all(gates.values()),'joint_strength_verified':False},indent=2)+'\n')
