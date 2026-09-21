"""Resolve only archived samples whose triangle bound exceeds the fixed criterion."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--archive',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
criterion=.2
plan={'criterion_mm':criterion,'method':'Keep triangle-bound proofs for samples <= criterion; directly superpose every remaining sample. No new FE solves.','stop':'One pass over all archived samples; no threshold changes.','limits':['Same linear isotropic single mesh and ideal clamp as source.','Nodal displacement only, not actual printed structure certification.','Latest mass not in archived loads.']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
units=[a.archive/f'unit_{i}.npz' for i in range(6)];u=np.array([np.load(p)['displacement_mm'] for p in units]);files=units.copy();rows=[];total=0;bounded=0;direct=0;upper=0.
for path in sorted(a.archive.glob('*_bounds.npz')):
 files.append(path)
 with np.load(path) as d:
  bounds=d['bounds'][:,0];w=d['wrench_N_Nmm'];t=d['time_s'];total+=len(t);mask=bounds<=criterion;bounded+=int(mask.sum())
  if mask.any():upper=max(upper,float(bounds[mask].max()))
  for j in np.flatnonzero(~mask):
   disp=np.tensordot(w[j],u,axes=(0,0));value=float(np.linalg.norm(disp,axis=1).max());assert value<=bounds[j]+1e-10
   upper=max(upper,value);direct+=1;rows.append({'source':str(path),'index':int(j),'time_s':float(t[j]),'triangle_bound_mm':float(bounds[j]),'direct_max_mm':value,'pass':value<=criterion})
assert total==bounded+direct and total>0
report={'samples':total,'triangle_proven_samples':bounded,'directly_resolved_samples':direct,'combined_archive_upper_mm':upper,'archive_nodal_displacement_pass':upper<=criterion,'direct_samples':rows,'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},'manufacturing_release':False}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['source_sha256','direct_samples']},indent=2))
