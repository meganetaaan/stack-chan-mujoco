"""Compare rounded-sole terminal joint state against same-time frozen baseline."""
import argparse,gzip,json,hashlib
from pathlib import Path
import mujoco,numpy as np
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();root=Path(__file__).resolve().parents[3];a.out.mkdir(parents=True,exist_ok=False);trial=root/'validation/rounded_sole_collision_v1/probe';base=root/'validation/foot_dynamics_capture_v1';model=root/'software/sim/mujoco/assets/r9_fast_turn_v1/models/scene.xml';m=mujoco.MjModel.from_xml_path(str(model));report=json.loads((trial/'report.json').read_text());rows=[]
with np.load(trial/'trace.npz') as t,np.load(base/'trace.npz') as b:
 time=float(t['time'][-1]);idx=int(np.argmin(abs(b['time']-time)));assert abs(b['time'][idx]-time)<1e-10
 for j,name in enumerate(report['joint_names']):
  joint=m.joint(name);q=float(t['qpos'][-1,int(joint.qposadr[0])]);qb=float(b['qpos'][idx,int(joint.qposadr[0])]);lo,hi=joint.range
  rows.append({'joint':name,'candidate_q_rad':q,'baseline_q_rad':qb,'difference_rad':q-qb,'limits_rad':[float(lo),float(hi)],'signed_margin_rad':float(min(q-lo,hi-q)),'reference_rad':float(t['reference_rad'][-1,j])})
contacts=[]
for label,path in [('candidate',trial),('baseline',base)]:
 with gzip.open(path/'foot_loads.jsonl.gz','rt') as f:
  for line in f:
   r=json.loads(line)
   if abs(r['time_s']-time)<1e-10:break
  else:raise ValueError('missing matched contact time')
 feet=[]
 for foot in r['feet']:
  R=np.array(foot['xmat']).reshape(3,3);pts=[];force=np.zeros(3)
  for c in r['contacts']:
   if foot['body_id'] not in c['body_ids']:continue
   sign=1 if c['body_ids'][1]==foot['body_id'] else -1;F=sign*np.array(c['frame']).reshape(3,3).T@np.array(c['raw_contact_force_torque'][:3]);force+=F;pts.append({'position_local_mm':(1000*R.T@(np.array(c['position_world_m'])-foot['xpos'])).tolist(),'normal_contact_force_N':c['raw_contact_force_torque'][0]})
  feet.append({'body_id':foot['body_id'],'contacts':pts,'force_world_N':force.tolist()})
 contacts.append({'case':label,'feet':feet})
r={'time_s':time,'joints':rows,'contacts':contacts,'cause_proven':False,'source_sha256':{str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [trial/'trace.npz',base/'trace.npz',model]}};(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps([x for x in rows if x['signed_margin_rad']<0],indent=2));print(json.dumps(contacts,indent=2))
