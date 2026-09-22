"""Direct-load solve to verify the selected unit-response superposition."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
import meshio
from skfem.io import from_meshio
from elasticity import analyze

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--bounds',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
source=json.loads((a.bounds/'report.json').read_text())
case=max(source['rows'],key=lambda r:r['selected_actual_displacement_mm'])
plan=json.loads((a.bounds/'plan.json').read_text())
(a.out/'plan.json').write_text(json.dumps({'case':case,'criteria':plan['criteria'],
 'relative_superposition_error_max':1e-8,'bounds_report_sha256':hashlib.sha256((a.bounds/'report.json').read_bytes()).hexdigest()},indent=2)+'\n')
mesh=from_meshio(meshio.read(a.bounds/'support.msh'))
w=np.array(case['selected_wrench_N_Nmm'])
report,data=analyze(mesh,lambda x:abs(x[0]+62.2)<1e-6,
 lambda x:(abs(x[2]-88)<1e-6)&(x[0]>=-29.5)&(x[0]<=4.5)&(x[1]>=16)&(x[1]<=36),
 [-5,26,62],w,plan['young_MPa'],plan['poisson'])
superposed={}
for key in ('displacement_mm','stress_MPa'):
 acc=np.zeros_like(data[key])
 for i in range(6):
  with np.load(a.bounds/f'unit_{i}.npz') as f:acc+=w[i]*f[key]
 superposed[key]=float(np.linalg.norm(data[key]-acc)/max(np.linalg.norm(data[key]),1e-30))
result={'case':case,'direct':report,'relative_superposition_errors':superposed,
 'superposition_verified':all(v<1e-8 for v in superposed.values()),
 'displacement_pass':report['max_displacement_mm']<=plan['criteria']['displacement_mm'],
 'stress_pass':max(report['max_absolute_principal_MPa'],report['max_von_mises_MPa'])<=plan['criteria']['stress_MPa'],
 'production_design_verified':False}
np.savez_compressed(a.out/'direct.npz',**data)
(a.out/'report.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
