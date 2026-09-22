"""Compare current and relieved shelf under one archived EPIC4 resultant."""
import argparse, hashlib, json
from pathlib import Path
import numpy as np
from elasticity import tetrahedralize, analyze
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--out',type=Path,required=True)
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
source=Path('validation/yaw_load_bounds_development_v1/yaw_load_direct_v1/report.json')
case=json.loads(source.read_text())['case']
plan={'question':'Does outer-port relief materially increase shelf deformation under the same archived load?',
 'source_case':case,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
 'material_assumption':{'young_MPa':1120,'poisson':.35},
 'fixed':'All boundary facets on rear mounting lands X=-62.2, ideal clamp.',
 'loaded':'Plate contact plane Z89, X[-37.5,11.6], Y[9.5,42.5]; resultant-preserving bonded traction, no unilateral contact.',
 'origin_mm':[-5,26,62],'mesh_sizes_mm':[3,2],
 'criteria':{'free_residual_N':1e-7,'energy_relative':1e-6,'mesh_displacement_relative':.1},
 'stop':'Exactly two shapes and two meshes for one archived load. Do not refine based on local peak stress.',
 'limits':['Archived EPIC4 load is not a current complete mass/load envelope.','E is a comparison assumption, not a printed ABS/PETG allowable.','No preload, contact separation, rear-body flexibility, creep, layer failure or bolt pullout.','No strength pass or manufacturing release.']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
rows=[];hashes={}
for name,path in [('old','validation/yaw_backing_keeper_v2/left_yaw_fixed_support.step'),('relief','validation/yaw_connector_shelf_relief_v2/left_yaw_fixed_support.step')]:
 hashes[path]=hashlib.sha256(Path(path).read_bytes()).hexdigest()
 for size in plan['mesh_sizes_mm']:
  mesh=tetrahedralize(path,a.out/f'{name}_{size}.msh',size)
  report,data=analyze(mesh,lambda x:abs(x[0]+62.2)<1e-6,
   lambda x:(abs(x[2]-89)<1e-6)&(x[0]>=-37.5)&(x[0]<=11.6)&(x[1]>=9.5)&(x[1]<=42.5),
   plan['origin_mm'],case['selected_wrench_N_Nmm'],1120,.35)
  report.update(shape=name,mesh_size_mm=size)
  report['numerical_balance_pass']=bool(report['free_residual_norm_N']<1e-7 and abs(2*report['strain_energy_Nmm']/report['external_work_Nmm']-1)<1e-6)
  rows.append(report)
  (a.out/'report.json').write_text(json.dumps({'source_sha256':hashes,'rows':rows,'manufacturing_release':False},indent=2)+'\n')
  print(name,size,report['max_displacement_mm'],report['external_work_Nmm'],flush=True)
metrics={}
for metric in ['max_displacement_mm','external_work_Nmm']:
 values={(r['shape'],r['mesh_size_mm']):r[metric] for r in rows}
 changes={s:abs(values[s,2]/values[s,3]-1) for s in ['old','relief']}
 metrics[metric]={'fine_relief_to_old_ratio':values['relief',2]/values['old',2],'mesh_relative_changes':changes}
result={'metrics':metrics,'numerical_balance_pass':all(r['numerical_balance_pass'] for r in rows),'displacement_comparison_eligible':max(metrics['max_displacement_mm']['mesh_relative_changes'].values())<=.1,'strength_verified':False,'manufacturing_release':False}
(a.out/'comparison.json').write_text(json.dumps(result,indent=2)+'\n')
