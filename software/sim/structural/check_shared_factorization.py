"""Compare the shared-factor solver against six archived independently solved fields."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
import meshio
from skfem.io import from_meshio
from elasticity import analyze_many
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--reference',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
mesh_path=a.reference/'support.msh'
plan=json.loads((a.reference/'plan.json').read_text())
(a.out/'plan.json').write_text(json.dumps({'scope':__doc__,'relative_field_error_max':1e-8,
 'sources_sha256':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in [mesh_path,*[a.reference/f'unit_{i}.npz' for i in range(6)]]}},indent=2)+'\n')
mesh=from_meshio(meshio.read(mesh_path));rows=[]
responses=analyze_many(mesh,lambda x:abs(x[0]+62.2)<1e-6,
 lambda x:(abs(x[2]-88)<1e-6)&(x[0]>=-29.5)&(x[0]<=4.5)&(x[1]>=16)&(x[1]<=36),
 [-5,26,62],np.eye(6),plan['young_MPa'],plan['poisson'])
for i,(report,data) in enumerate(responses):
 with np.load(a.reference/f'unit_{i}.npz') as ref:
  assert np.array_equal(data['nodes_mm'],ref['nodes_mm'])
  errors={k:float(np.linalg.norm(data[k]-ref[k])/max(np.linalg.norm(ref[k]),1e-30)) for k in ['displacement_mm','stress_MPa','load_N','reaction_N']}
 rows.append({'unit':i,'relative_errors':errors,'passed':all(x<1e-8 for x in errors.values())})
result={'scope':__doc__,'rows':rows,'passed':all(r['passed'] for r in rows)}
(a.out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if not result['passed']:raise SystemExit(1)
