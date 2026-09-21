"""Estimate candidate battery force on mount from frozen base pose histories."""
import argparse, hashlib, json
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
def estimate_force(t,q,mass=.076,center=(.029,0,.080)):
 rotation=Rotation.from_quat(q[:,[4,5,6,3]])
 position=q[:,:3]+rotation.apply(np.tile(center,(len(t),1)))
 acceleration=np.gradient(np.gradient(position,t,axis=0,edge_order=2),t,axis=0,edge_order=2)
 return position,rotation.inv().apply(mass*(np.array([0,0,-9.81])-acceleration))

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);out=p.parse_args().out;out.mkdir(parents=True,exist_ok=False)
 rows=[]
 for path in sorted(Path('validation/prototype_epic4_v1').glob('actuator_fullbody_load_*/trace.npz')):
  with np.load(path) as d:t=d['time'];q=d['qpos']
  assert q.shape==(len(t),19) and np.isfinite(q).all() and (np.diff(t)>0).all()
  assert np.allclose(np.linalg.norm(q[:,3:7],axis=1),1,atol=1e-6)
  position,force=estimate_force(t,q)
  valid=np.arange(2,len(t)-2);i=int(valid[np.argmax(np.linalg.norm(force[valid],axis=1))])
  np.savez_compressed(out/(path.parent.name+'.npz'),time=t,force_on_mount_base_N=force,position_world_m=position,interior_indices=valid)
  rows.append({'source':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'dt_min_s':float(np.diff(t).min()),'dt_max_s':float(np.diff(t).max()),'peak_index':i,'peak_time_s':float(t[i]),'peak_force_norm_N':float(np.linalg.norm(force[i])),'simultaneous_force_base_N':force[i].tolist()})
 (out/'report.json').write_text(json.dumps({'status':'estimated_force_only_not_strength_acceptance','mass_kg':.076,'battery_center_base_m':[.029,0,.08],'method':'two second-order gradients of transformed center; discard two endpoints each side','limitations':['Frozen original mass motion, not updated full-body dynamics','Sampling and differentiation can miss or distort impact peaks','Rotational inertia moment and preload absent','No stop or fall qualification'],'cases':rows},indent=2)+'\n');print(rows)

if __name__=="__main__":main()
