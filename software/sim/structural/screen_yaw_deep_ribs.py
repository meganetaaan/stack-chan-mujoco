"""Bounded deformation check of deeper ribs under the archived shelf load."""
import argparse,hashlib,json
from pathlib import Path
from elasticity import tetrahedralize,analyze
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--step',type=Path,default=Path('validation/yaw_deep_side_ribs_v1/left_yaw_fixed_support.step'));a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
source=Path('validation/yaw_shelf_compliance_v1/plan.json');old=json.loads(source.read_text());step=a.step
plan={'question':'Does the supplied support meet the existing 0.2 mm deformation allocation for the archived comparison load?',
 'source_plan':str(source),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'step':str(step),'step_sha256':hashlib.sha256(step.read_bytes()).hexdigest(),
 'load_and_boundary_conditions':old,'criterion_max_displacement_mm':.2,'mesh_relative_limit':.1,
 'stop':'3 mm mesh first. If displacement exceeds 0.2 mm, stop as unmet; otherwise run 2 mm once and require both meshes <=0.2 mm and relative change <=10%. No stress-driven refinement.',
 'limits':['One archived load only; latest mass and full load envelope absent','Assumed isotropic print material; no certified allowable','Bonded distributed load and ideal rear clamp; no actual joint contact','Shroud rail seat is not bonded or assigned tensile support; only the unchanged rear clamp is supported','Not manufacturing release']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');rows=[]
for size in [3,2]:
 mesh=tetrahedralize(step,a.out/f'support_{size}.msh',size)
 r,_=analyze(mesh,lambda x:abs(x[0]+62.2)<1e-6,
 lambda x:(abs(x[2]-89)<1e-6)&(x[0]>=-37.5)&(x[0]<=11.6)&(x[1]>=9.5)&(x[1]<=42.5),
 old['origin_mm'],old['source_case']['selected_wrench_N_Nmm'],1120,.35)
 r['mesh_size_mm']=size;rows.append(r);print(json.dumps(r),flush=True)
 if r['max_displacement_mm']>.2:break
balance=all(r['free_residual_norm_N']<1e-7 and abs(2*r['strain_energy_Nmm']/r['external_work_Nmm']-1)<1e-6 for r in rows)
change=abs(rows[-1]['max_displacement_mm']/rows[0]['max_displacement_mm']-1) if len(rows)==2 else None
result={'rows':rows,'numerical_balance_pass':balance,'mesh_relative_change':change,'archived_case_displacement_screen_pass':bool(balance and len(rows)==2 and change<=.1 and all(r['max_displacement_mm']<=.2 for r in rows)),'manufacturing_release':False}
(a.out/'report.json').write_text(json.dumps(result,indent=2)+'\n')
