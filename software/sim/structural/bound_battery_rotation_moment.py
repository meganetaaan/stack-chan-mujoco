"""Conditional inertia moment bound; assumes battery COM at geometric center."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);out=p.parse_args().out;out.mkdir(parents=True,exist_ok=False)
mass=.076;half=np.array([.011,.030,.015]);imax=float(mass*np.dot(half,half));rows=[]
for path in sorted(Path('validation/prototype_epic4_v1').glob('actuator_fullbody_load_*/trace.npz')):
 with np.load(path) as d:t=d['time'];q=d['qpos']
 r=Rotation.from_quat(q[:,[4,5,6,3]])
 dt=np.diff(t);omega=(r[1:]*r[:-1].inv()).as_rotvec()/dt[:,None];tm=(t[1:]+t[:-1])/2
 alpha=np.gradient(omega,tm,axis=0,edge_order=2)
 bound=imax*(np.linalg.norm(alpha,axis=1)+np.linalg.norm(omega,axis=1)**2)
 valid=np.arange(2,len(tm)-2);i=int(valid[np.argmax(bound[valid])])
 rows.append({'source':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'peak_bound_Nm':float(bound[i]),'midpoint_time_s':float(tm[i]),'omega_world_rad_s':omega[i].tolist(),'alpha_world_rad_s2':alpha[i].tolist()})
(out/'report.json').write_text(json.dumps({'scope':'Conditional screening bound, not qualified load','inertia_spectral_upper_kg_m2':imax,'assumptions':['COM at geometric center','All 76g lies within 22x60x30mm box','Differentiated sampled rotations represent actual angular motion'],'formula':'norm(I alpha + omega cross I omega) <= m radius_max^2 (norm(alpha) + norm(omega)^2)','cases':rows},indent=2)+'\n');print(imax,rows)
