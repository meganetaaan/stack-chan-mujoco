"""Necessary rectangular support bounds for static ankle-balancing sole loads."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();root=Path(__file__).resolve().parents[3];a.out.mkdir(parents=True,exist_ok=False)
source=root/'validation/ankle_mount_load_mapping_v1';meta=json.loads((source/'report.json').read_text())
plan={'scope':__doc__,'normal_force_threshold_N':1e-6,'geometric_tolerance_mm':1e-6,'rectangle_mm':{'x':[-39,47],'left_y':[-18,30],'right_y':[-30,18]},'formula':'At z=-19: x_COP=1-My/Fz, y_COP=side*6+Mx/Fz; shift moment from z=-16 before calculation.','limitations':['Necessary bound only: rounded corners and holes may further restrict contact.','Ignores inertia and actual floor contact; failure rejects the static balancing assumption, not the robot.','No friction or yaw moment feasibility proof.']};(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');rows=[]
for case in meta['cases']:
 f=source/(case['name']+'.npz')
 with np.load(f) as d:w=-d['wrench_N_Nmm'].copy();time=d['time_s']
 w[:,3:]-=np.cross([0,0,-3],w[:,:3]);mask=w[:,2]>1e-6;ids=np.flatnonzero(mask);cop=np.column_stack((1-w[mask,4]/w[mask,2],(6 if case['side']=='left' else -6)+w[mask,3]/w[mask,2]));lo=np.array([-39,plan['rectangle_mm'][case['side']+'_y'][0]]);hi=np.array([47,plan['rectangle_mm'][case['side']+'_y'][1]]);outside=np.maximum(np.maximum(lo-cop,cop-hi),0).max(axis=1);bad=outside>1e-6
 worst=None
 if len(ids):
  j=int(outside.argmax());idx=int(ids[j]);worst={'index':idx,'time_s':float(time[idx]),'cop_mm':cop[j].tolist(),'outside_mm':float(outside[j]),'simultaneous_wrench_N_Nmm':w[idx].tolist()}
 rows.append({'case':case['name'],'source_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'samples':len(w),'positive_normal_samples':len(ids),'outside_rectangle_samples':int(bad.sum()),'negative_normal_samples':int((w[:,2]<-1e-6).sum()),'worst':worst})
probe=json.loads((root/'validation/full_yoke_screen_h2_v1/plan.json').read_text());w=np.array(probe['wrench_N_Nmm']);cop=[1-w[4]/w[2],6+w[3]/w[2]]
r={'cases':rows,'screened_FE_case':{'cop_mm':cop,'rectangle_y_min_mm':-18,'below_y_edge_mm':-18-cop[1],'compression_only_static_balance_possible':bool(-39<=cop[0]<=47 and -18<=cop[1]<=30)},'joint_verified':False};(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r['screened_FE_case'],indent=2))
