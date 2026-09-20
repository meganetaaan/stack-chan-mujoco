"""Transform recorded contacts to ankle-roll CAD coordinates, preserving all moments."""
import argparse,gzip,hashlib,json,sys
from pathlib import Path
import numpy as np
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--source',type=Path,help='Directory containing foot_loads.jsonl.gz');p.add_argument('--model',type=Path);a=p.parse_args();root=Path(__file__).resolve().parents[3];a.out.mkdir(parents=True,exist_ok=False);src=(a.source or root/'validation/foot_dynamics_capture_v1')/'foot_loads.jsonl.gz'
sys.path.insert(0,str(root/'software/sim/actuator'));from fixtures import full_body
sim,_=full_body(model_path=a.model);model=sim.m;hierarchy=[]
for side in ['left','right']:
 b=int(model.joint(side+'_ankle_roll').bodyid[0]);children=np.flatnonzero(model.body_parentid==b).tolist();hierarchy.append({'side':side,'body_id':b,'children':children});assert not children
plan={'source_path':str(src),'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'criteria':{'force_residual_N':1e-8,'moment_residual_Nmm':1e-5},'model_directory':str(a.model) if a.model else 'frozen r9','hierarchy':hierarchy,'axes':'ankle_roll body local axes; positions mm, forces N, moments N mm','limitations':['Rigid recorded foot; finite contact areas and TPU deformation are not inferred.','Wrench at yoke plane preserves resultant only, not traction distribution.','Entire foot inertia cannot be applied solely to yoke material.']};(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');times=[];loads=[];errors=[];selected=None
with gzip.open(src,'rt') as f,gzip.open(a.out/'contacts_local.jsonl.gz','wt') as out:
 for idx,line in enumerate(f):
  row=json.loads(line);local=[];wrenches=[]
  for side,foot in zip(['left','right'],row['feet']):
   R=np.array(foot['xmat']).reshape(3,3);origin=np.array(foot['xpos']);center=np.array([1,6 if side=='left' else -6,-19]);total=np.zeros(6);contacts=[]
   for c in row['contacts']:
    if foot['body_id'] not in c['body_ids']:continue
    sign=1 if c['body_ids'][1]==foot['body_id'] else -1;frame=np.array(c['frame']).reshape(3,3);raw=np.array(c['raw_contact_force_torque']);pos=1000*(R.T@(np.array(c['position_world_m'])-origin));force=sign*R.T@frame.T@raw[:3];torque=1000*sign*R.T@frame.T@raw[3:];total+=np.r_[force,torque+np.cross(pos-center,force)];contacts.append({'position_mm':pos.tolist(),'force_N':force.tolist(),'contact_couple_Nmm':torque.tolist()})
   ext=np.array(foot['cfrc_ext']);ef=R.T@ext[3:];em=1000*R.T@(ext[:3]+np.cross(np.array(foot['subtree_com_root'])-origin,ext[3:]))-np.cross(center,ef);errors.append(total-np.r_[ef,em]);wrenches.append(total);local.append({'side':side,'contacts':contacts,'wrench_at_yoke_center_N_Nmm':total.tolist()})
  out.write(json.dumps({'time_s':row['time_s'],'feet':local})+'\n');times.append(row['time_s']);loads.append(wrenches)
  if idx==2446:selected=local
e=np.array(errors);r={'samples':len(times),'maximum_force_residual_N':float(abs(e[:,:3]).max()),'maximum_moment_residual_Nmm':float(abs(e[:,3:]).max()),'selected_sample_2446':selected,'structural_load_distribution_verified':False};r['transform_pass']=r['maximum_force_residual_N']<=1e-8 and r['maximum_moment_residual_Nmm']<=1e-5
np.savez_compressed(a.out/'wrenches.npz',time_s=times,wrench_N_Nmm=loads);(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
