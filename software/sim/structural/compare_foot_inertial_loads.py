"""Same-kinematics inverse-dynamics delta from the foot inertia replacement."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
import mujoco
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
paths=[Path('outputs/rounded_sole_fine_v1/models/scene.xml'),Path('validation/foot_inertia_model_v2/scene.xml')]
models=[mujoco.MjModel.from_xml_path(str(x)) for x in paths];data=[mujoco.MjData(m) for m in models]
assert models[0].nq==models[1].nq and models[0].nv==models[1].nv
names=[mujoco.mj_id2name(models[0],mujoco.mjtObj.mjOBJ_JOINT,j) for j in range(models[0].njnt)]
assert names==[mujoco.mj_id2name(models[1],mujoco.mjtObj.mjOBJ_JOINT,j) for j in range(models[1].njnt)]
def rne(m,d,q,v,acc):
 d.qpos[:]=q;d.qvel[:]=v
 mujoco.mj_forward(m,d)
 d.qacc[:]=acc
 force=np.empty(m.nv);mujoco.mj_rne(m,d,1,force)
 return force
# Verify known static gravitational delta in the free root translational coordinates.
zeros=np.zeros(models[0].nv)
g=[rne(m,d,m.qpos0,zeros,zeros) for m,d in zip(models,data)]
mass_delta=models[1].body_mass.sum()-models[0].body_mass.sum()
assert np.allclose((g[1]-g[0])[:3],-mass_delta*models[0].opt.gravity,rtol=0,atol=1e-10)
a.out.mkdir(parents=True,exist_ok=False);rows=[];hashes={str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in paths}
for turn in ['left','right']:
 path=Path(f'validation/prototype_epic4_v1/actuator_fullbody_load_{turn}_v1/trace.npz');hashes[str(path)]=hashlib.sha256(path.read_bytes()).hexdigest()
 with np.load(path) as z:t=z['time'];q=z['qpos'];v=z['qvel']
 assert q.shape==(len(t),models[0].nq) and v.shape==(len(t),models[0].nv)
 assert np.all(np.diff(t)>0) and np.isfinite(q).all() and np.isfinite(v).all()
 acc=np.gradient(v,t,axis=0);delta=np.empty_like(v)
 for i in range(len(t)):
  delta[i]=rne(models[1],data[1],q[i],v[i],acc[i])-rne(models[0],data[0],q[i],v[i],acc[i])
 assert np.isfinite(delta).all()
 np.savez_compressed(a.out/(turn+'.npz'),time_s=t,required_generalized_force_delta=delta)
 peaks=[]
 # Omit one-sided endpoint acceleration estimates from peak selection.
 for j,name in enumerate(names):
  if j==0:continue
  k=models[0].jnt_dofadr[j];i=int(np.argmax(abs(delta[1:-1,k])))+1
  peaks.append({'joint':name,'peak_abs_delta_Nm':float(abs(delta[i,k])),'signed_delta_Nm':float(delta[i,k]),'sample':i,'time_s':float(t[i])})
 rows.append({'turn':turn,'joint_peaks':peaks,'max_free_root_force_delta_N':float(np.linalg.norm(delta[1:-1,:3],axis=1).max())})
r={'sources_sha256':hashes,'rows':rows,'mass_delta_kg':float(mass_delta),'static_gravity_delta_check':True,'mujoco_version':mujoco.__version__,'physical_load_qualification':False,'limits':['Mass and density assumptions inherited from foot_inertia_model_v2.', 'Kinematics are retained EPIC4 trajectories, not trajectories generated with updated mass.', 'Acceleration uses sampled qvel finite differences, including contact-induced changes; endpoints excluded from maxima.', 'RNE force contains inertia, Coriolis and gravity; contact, passive and external forces are not solved as new support loads.', 'These deltas must not be substituted for full joint interface wrenches or strength load cases.', 'Only foot inertia changes are represented; whole robot payload, current collision geometry and coordinate audit remain.']}
(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({x['turn']:max(y['peak_abs_delta_Nm'] for y in x['joint_peaks']) for x in rows}))
