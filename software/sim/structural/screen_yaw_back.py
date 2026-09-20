"""Check a revised yaw back against the previously failed load, including mesh convergence."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from elasticity import tetrahedralize,analyze
ROOT=Path(__file__).resolve().parents[3]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--step',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
source=ROOT/'validation/yaw_load_bounds_development_v1/yaw_load_direct_v1/report.json'
case=json.loads(source.read_text())['case']
plan=dict(scope=__doc__,geometry_sha256=hashlib.sha256(a.step.read_bytes()).hexdigest(),source_case=case,
          source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),mesh_mm=[4.,3.,2.],young_MPa=1120.,poisson=.35,
          fixed='rear mounting lands x=-62.2 mm ideal clamp',load='shelf z=88 mm x[-29.5,4.5] y[16,36]',
          criteria=dict(displacement_mm=.2,stress_MPa=5.6,displacement_mesh_relative=.05,stress_mesh_relative=.1))
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
rows=[]
for size in plan['mesh_mm']:
 mesh=tetrahedralize(a.step,a.out/f'support_{size}.msh',size)
 report,data=analyze(mesh,lambda x:abs(x[0]+62.2)<1e-6,
  lambda x:(abs(x[2]-88)<1e-6)&(x[0]>=-29.5)&(x[0]<=4.5)&(x[1]>=16)&(x[1]<=36),
  [-5,26,62],case['selected_wrench_N_Nmm'],plan['young_MPa'],plan['poisson'])
 report['mesh_mm']=size;rows.append(report)
 np.savez_compressed(a.out/f'support_{size}.npz',**data)
 print(json.dumps(report),flush=True)
r=rows[-1];previous=rows[-2]
gates=dict(displacement=r['max_displacement_mm']<=.2,
 stress=max(r['max_absolute_principal_MPa'],r['max_von_mises_MPa'])<=5.6,
 displacement_mesh=abs(r['max_displacement_mm']/previous['max_displacement_mm']-1)<=.05,
 stress_mesh=abs(r['max_absolute_principal_MPa']/previous['max_absolute_principal_MPa']-1)<=.1)
result=dict(scope=__doc__,rows=rows,gates=gates,passed_screen=all(gates.values()),production_verified=False,
 limitations=['one previously failed load only','clamped lands, no mating structure/contact','no buckling','mass update and full load envelope pending'])
(a.out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(gates),flush=True)
