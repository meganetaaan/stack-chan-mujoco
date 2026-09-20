"""Local boot nut-seat compression screen with explicitly idealized bearing supports."""
import argparse,hashlib,json
from pathlib import Path
import cadquery as cq
import numpy as np
from elasticity import tetrahedralize,analyze
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[3]
if a.out.exists():p.error('new output required')
a.out.mkdir(parents=True)
source=root/'validation/boot_low_head_candidate_v1/cad/left_boot_shell.step'
plan={'scope':__doc__,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'crop_mm':{'x':[-38,-30],'y':[-18.5,-10.5],'z':[-16,-12.8]},'mesh_mm':[1,.7,.5],'load_N':20,'young_MPa':1120,'poisson':.35,'fixed':'All pad bottom facets z=-16 ideal clamp','load':'Entire cavity floor z=-14.6, downward 20 N; larger than actual nut bearing area','criteria':{'displacement_mm':.2,'stress_MPa':5.6,'last_displacement_relative_change':.05,'last_stress_relative_change':.1},'limitations':['Single left rear local submodel, not whole boot or full joint.','Cut boundaries free; omitted surrounding material changes stiffness.','Load smeared over cavity floor, no contact/preload solution.','Isotropic PETG constants and allowable are unqualified assumptions; no creep/buckling.']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
shape=cq.importers.importStep(str(source)).val().intersect(cq.Workplane('XY').box(8,8,3.2).val().translate((-34,-14.5,-14.4)))
if not shape.isValid() or len(shape.Solids())!=1:raise ValueError('invalid local crop')
step=a.out/'local_seat.step';cq.exporters.export(shape,str(step));rows=[]
for size in plan['mesh_mm']:
 mesh=tetrahedralize(step,a.out/f'seat_{size}.msh',size)
 report,data=analyze(mesh,lambda x:abs(x[2]+16)<1e-6,lambda x:abs(x[2]+14.6)<1e-6,[-34,-14.5,-14.6],[0,0,-20,0,0,0],1120,.35)
 report['mesh_mm']=size;rows.append(report);np.savez_compressed(a.out/f'seat_{size}.npz',**data)
 print(json.dumps(report),flush=True)
r,b=rows[-1],rows[-2]
gates={'displacement':r['max_displacement_mm']<=.2,'stress':max(r['max_von_mises_MPa'],r['max_absolute_principal_MPa'])<=5.6,'displacement_convergence':abs(r['max_displacement_mm']/b['max_displacement_mm']-1)<=.05,'stress_convergence':abs(r['max_absolute_principal_MPa']/b['max_absolute_principal_MPa']-1)<=.1}
(a.out/'report.json').write_text(json.dumps({'rows':rows,'gates':gates,'local_screen_pass':all(gates.values()),'joint_strength_verified':False,'manufacturing_release':False},indent=2)+'\n')
