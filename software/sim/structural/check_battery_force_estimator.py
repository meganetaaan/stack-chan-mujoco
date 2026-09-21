"""Analytic checks for battery-on-mount force sign, frame and differentiation."""
import argparse,json
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from estimate_battery_translation_load import estimate_force
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);out=p.parse_args().out;out.mkdir(parents=True,exist_ok=False)
t=np.arange(1001)*.001
base=np.zeros((len(t),19));base[:,3]=1
cases=[]
# Thresholds defined before evaluation: roundoff checks and smooth rotation truncation.
for name in ['static','free_fall','rotated_static','constant_yaw']:
 q=base.copy();expected=np.tile([0,0,-.076*9.81],(len(t),1));tol=1e-7
 if name=='free_fall':q[:,2]=-.5*9.81*t*t;expected[:]=0
 if name=='rotated_static':
  r=Rotation.from_euler('x',90,degrees=True);v=r.as_quat();q[:,3:7]=v[[3,0,1,2]];expected=r.inv().apply(expected)
 if name=='constant_yaw':
  omega=2.;v=Rotation.from_rotvec(np.column_stack([np.zeros_like(t),np.zeros_like(t),omega*t])).as_quat();q[:,3:7]=v[:,[3,0,1,2]];expected[:,0]=.076*omega**2*.029;tol=1e-6
 _,force=estimate_force(t,q);error=float(np.max(np.abs(force[2:-2]-expected[2:-2])))
 cases.append({'case':name,'max_component_error_N':error,'limit_N':tol,'pass':error<=tol})
(out/'report.json').write_text(json.dumps({'scope':'analytic smooth-motion algorithm checks, not structural or measured validation','cases':cases},indent=2)+'\n');print(cases)
assert all(c['pass'] for c in cases)
