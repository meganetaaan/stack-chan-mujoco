"""Check recorded foot spatial balance and independently summed contact wrench."""
import argparse,gzip,json,hashlib
from pathlib import Path
import numpy as np
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--source',type=Path,help='Directory containing foot_loads.jsonl.gz');a=p.parse_args();root=Path(__file__).resolve().parents[3];src=(a.source or root/'validation/foot_dynamics_capture_v1')/'foot_loads.jsonl.gz';a.out.mkdir(parents=True,exist_ok=False)
plan={'source_path':str(src),'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'criteria':{'force_residual_N':1e-8,'moment_residual_Nm':1e-8},'convention':'World axes at subtree COM, torque then force. cacc includes gravity convention of MuJoCo.','formula':'I*a + v cross_force (I*v) = cfrc_int + cfrc_ext for leaf body','reference':'https://raw.githubusercontent.com/google-deepmind/mujoco/3.3.0/src/engine/engine_util_spatial.c','limitations':['Recorded model only; leaf-body and applied-force assumptions require model audit.','No structural strength claim.']};(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
def mul(i,v):
 J=np.array([[i[0],i[3],i[4]],[i[3],i[1],i[5]],[i[4],i[5],i[2]]]);h=i[6:9]
 return np.r_[J@v[:3]+np.cross(h,v[3:]),i[9]*v[3:]-np.cross(h,v[:3])]
errors=[];contact_errors=[];selected=[]
with gzip.open(src,'rt') as f:
 for index,line in enumerate(f):
  row=json.loads(line)
  for foot in row['feet']:
   v=np.array(foot['cvel']);ia=mul(foot['cinert'],np.array(foot['cacc']));iv=mul(foot['cinert'],v);inert=ia+np.r_[np.cross(v[:3],iv[:3])+np.cross(v[3:],iv[3:]),np.cross(v[:3],iv[3:])];internal=np.array(foot['cfrc_int']);external=np.array(foot['cfrc_ext']);errors.append(inert-internal-external)
   total=np.zeros(6)
   for c in row['contacts']:
    if foot['body_id'] not in c['body_ids']:continue
    sign=1 if c['body_ids'][1]==foot['body_id'] else -1;R=np.array(c['frame']).reshape(3,3);raw=np.array(c['raw_contact_force_torque']);force=sign*R.T@raw[:3];moment=sign*R.T@raw[3:]+np.cross(np.array(c['position_world_m'])-foot['subtree_com_root'],force);total+=np.r_[moment,force]
   contact_errors.append(total-external)
   if index==2446:selected.append({'body_id':foot['body_id'],'inertial_wrench':inert.tolist(),'joint_wrench':internal.tolist(),'external_wrench':external.tolist(),'contact_wrench':total.tolist()})
e=np.array(errors);c=np.array(contact_errors);r={'body_samples':len(e),'maximum_balance_force_residual_N':float(abs(e[:,3:]).max()),'maximum_balance_moment_residual_Nm':float(abs(e[:,:3]).max()),'maximum_contact_force_residual_N':float(abs(c[:,3:]).max()),'maximum_contact_moment_residual_Nm':float(abs(c[:,:3]).max()),'selected_sample_2446':selected,'joint_strength_verified':False};r['numerical_balance_pass']=max(r[k] for k in r if 'residual' in k)<=1e-8;(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
