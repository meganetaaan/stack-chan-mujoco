"""Three-mesh FE screen of jig core under any force vector of magnitude <= 1 N."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from elasticity import tetrahedralize,analyze_many
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--step',type=Path,required=True);p.add_argument('--nut-z-mm',type=float,required=True);p.add_argument('--out',type=Path,required=True)
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
plan={'scope':__doc__,'geometry_sha256':hashlib.sha256(a.step.read_bytes()).hexdigest(),
      'young_MPa':180000.,'poisson':.3,'force_radius_N':1.,'origin_mm':[-54.8,57,a.nut_z_mm],
      'fixed':'shaft end x=80 mm; ideal handle grip','loaded':'hub face y=51 mm, resulting wrench at nut center',
      'mesh_mm':[3.,2.,1.5],'criteria':{'displacement_mm':.1,'stress_MPa':100.,'free_residual_N':1e-6,'relative_mesh_displacement':.05,'relative_mesh_stress':.1},
      'material_basis':'conditional stainless steel candidate: E=200GPa typical reduced 10%, nu assumed; stress allowable 100MPa provisional, purchased material and joints unqualified',
      'limitations':['no spring fingers or their contacts','no handle/joint compliance','no material/preload/force qualification','distributed resultant on hub, not actual finger contact stress','single monolithic elastic core']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
rows=[]
for size in plan['mesh_mm']:
    mesh=tetrahedralize(a.step,a.out/f'core_{size}.msh',size)
    w=np.zeros((3,6));w[:,:3]=np.eye(3)
    fields=[];reports=[]
    for i,(report,data) in enumerate(analyze_many(mesh,lambda x:abs(x[0]-80)<1e-6,lambda x:abs(x[1]-51)<1e-6,plan['origin_mm'],w,plan['young_MPa'],plan['poisson'])):
        fields.append(data['displacement_mm'].copy());reports.append(report)
        np.savez_compressed(a.out/f'mesh_{size}_force_{i}.npz',**data)
    # Exact displacement operator norm at every saved quadratic displacement node.
    response=np.stack(fields,axis=-1)
    singular=np.linalg.svd(response,compute_uv=False)
    maximum=float(singular[:,0].max())
    # Triangle inequality and Cauchy-Schwarz for principal/von-Mises norms.
    stress_bounds={key:float(np.linalg.norm([r[key] for r in reports])) for key in ['max_absolute_principal_MPa','max_von_mises_MPa']}
    row={'mesh_mm':size,'any_force_max_nodal_displacement_mm':maximum,'stress_upper_bounds_MPa':stress_bounds,'unit_reports':reports,
         'equilibrium_passed':all(r['free_residual_norm_N']<=1e-6 for r in reports)}
    rows.append(row);print(json.dumps({k:v for k,v in row.items() if k!='unit_reports'}),flush=True)
last,previous=rows[-1],rows[-2]
changes={'displacement':abs(last['any_force_max_nodal_displacement_mm']-previous['any_force_max_nodal_displacement_mm'])/last['any_force_max_nodal_displacement_mm']}
changes.update({key:abs(last['stress_upper_bounds_MPa'][key]-previous['stress_upper_bounds_MPa'][key])/last['stress_upper_bounds_MPa'][key] for key in last['stress_upper_bounds_MPa']})
gates={'displacement':all(r['any_force_max_nodal_displacement_mm']<=.1 for r in rows),
       'stress':all(max(r['stress_upper_bounds_MPa'].values())<=100 for r in rows),
       'equilibrium':all(r['equilibrium_passed'] for r in rows),'displacement_convergence':changes['displacement']<=.05,
       'stress_convergence':all(v<=.1 for k,v in changes.items() if k!='displacement')}
report={'scope':__doc__,'rows':rows,'last_two_relative_changes':changes,'gates':gates,'passed_core_screen':all(gates.values()),
        'jig_verified':False,'note':'nodal displacement bound does not certify displacement extrema inside elements or the omitted compliant components'}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(gates))
