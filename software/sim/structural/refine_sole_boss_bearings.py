"""Refine nominal boss bearing preload and locate unfiltered principal stress peaks."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np,meshio
from skfem.io import from_meshio
from elasticity import analyze
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();root=Path(__file__).resolve().parents[3];src=root/'validation/sole_boss_bearing_mesh_v1';a.out.mkdir(parents=True,exist_ok=False)
plan={'scope':__doc__,'mesh_mm':[.7,.5],'force_N':20,'criteria':{'displacement_mm':.2,'principal_MPa':5.6,'relative_displacement':.05,'relative_stress':.1},'limitations':['Bilateral normal support, not unilateral contact.','Rigid spacer, cropped boss, assumed isotropic PETG; no creep or walking load.']};(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');rows=[]
for h in plan['mesh_mm']:
 f=src/f'boss_{h}.msh';mesh=from_meshio(meshio.read(f));r,arr=analyze(mesh,'spacer_bearing','nut_bearing',[35,6,-14.2],[0,0,-20,0,0,0],young=1120,poisson=.35,support_mode='normal_z');stress=np.moveaxis(arr['stress_MPa'],(0,1),(-2,-1));principal=abs(np.linalg.eigvalsh(stress)).max(axis=-1);idx=np.unravel_index(principal.argmax(),principal.shape);r.update(mesh_mm=h,mesh_sha256=hashlib.sha256(f.read_bytes()).hexdigest(),peak_position_mm=arr['quadrature_coordinates_mm'][:,idx[0],idx[1]].tolist());rows.append(r);np.savez_compressed(a.out/f'fields_{h}.npz',**arr);(a.out/f'report_{h}.json').write_text(json.dumps(r,indent=2)+'\n')
c,f=rows;changes={'displacement':abs(f['max_displacement_mm']/c['max_displacement_mm']-1),'stress':abs(f['max_absolute_principal_MPa']/c['max_absolute_principal_MPa']-1)};r={'rows':rows,'relative_change':changes,'gates':{'displacement':f['max_displacement_mm']<=.2,'stress':f['max_absolute_principal_MPa']<=5.6,'displacement_convergence':changes['displacement']<=.05,'stress_convergence':changes['stress']<=.1},'joint_verified':False};(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'changes':changes,'gates':r['gates'],'fine_stress_MPa':f['max_absolute_principal_MPa'],'peak_position_mm':f['peak_position_mm']},indent=2))
