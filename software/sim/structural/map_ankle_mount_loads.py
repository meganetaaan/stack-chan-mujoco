"""Shift all EPIC4 ankle-roll wrenches to the boot mounting-plane center."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();root=Path(__file__).resolve().parents[3];a.out.mkdir(parents=True,exist_ok=False)
plan={'scope':__doc__,'mount_center_mm':{'left':[1,6,-16],'right':[1,-6,-16]},'convention':'Parent-on-child, axes unchanged from ankle_roll body. M_at_center = M_at_joint - center cross F.','criteria':{'maximum_reconstruction_error_Nmm':1e-9},'limitations':['Equivalent interface wrench only: not the load borne by each screw or boot seat.','Foot component inertia and ground-contact load path must be included before distributing forces.','Frozen EPIC4 geometry/mass; revised CAD requires new dynamics.','No safety multiplier applied; fixture cases retained separately from fullbody cases.']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');src=root/'validation/prototype_epic4_v1';paths=sorted((src/'actuator_suite_v2').glob('*/trace.npz'))+sorted(src.glob('actuator_fullbody_load_*/trace.npz'));assert paths;rows=[]
for path in paths:
 report=json.loads(path.with_name('report.json').read_text());names=report['joint_names']
 with np.load(path) as d:time=d['time'];allw=d['joint_wrench_local_force_moment']
 for side in ['left','right']:
  name=side+'_ankle_roll'
  if name not in names:continue
  w=allw[:,names.index(name)].copy();assert np.isfinite(w).all();w[:,3:]*=1000;original=w.copy();c=np.array(plan['mount_center_mm'][side]);w[:,3:]-=np.cross(c,w[:,:3]);err=float(abs(w[:,3:]+np.cross(c,w[:,:3])-original[:,3:]).max());assert err<=1e-9
  tag=path.parent.name+'_'+side;np.savez_compressed(a.out/(tag+'.npz'),time_s=time,wrench_N_Nmm=w)
  peaks=[]
  for k in range(6):
   for label,index in [('min',int(w[:,k].argmin())),('max',int(w[:,k].argmax()))]:peaks.append({'component':k,'extreme':label,'index':index,'time_s':float(time[index]),'simultaneous_wrench_N_Nmm':w[index].tolist()})
  rows.append({'name':tag,'source':str(path.relative_to(root)),'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'side':side,'samples':len(time),'fixture':report.get('mode','fullbody'),'reconstruction_error_Nmm':err,'peak_force_norm_N':float(np.linalg.norm(w[:,:3],axis=1).max()),'peak_moment_norm_Nmm':float(np.linalg.norm(w[:,3:],axis=1).max()),'extremes':peaks})
r={'cases':rows,'total_samples':sum(x['samples'] for x in rows),'load_distribution_verified':False,'joint_strength_verified':False};(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'cases':len(rows),'samples':r['total_samples'],'peak_force_N':max(x['peak_force_norm_N'] for x in rows),'peak_moment_Nmm':max(x['peak_moment_norm_Nmm'] for x in rows)}))
