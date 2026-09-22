"""Summarize bounded low-voltage probes without promoting them to acceptance tests."""
import argparse,hashlib,json,platform
from pathlib import Path
import numpy as np
import mujoco
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);a=p.parse_args();rows=[]
for side,sign in [('left',1),('right',-1)]:
 path=a.root/side;report=json.loads((path/'report.json').read_text())
 oldpath=Path(f'validation/prototype_epic4_v1/actuator_fullbody_load_{side}_v1/report.json');old=json.loads(oldpath.read_text())
 with np.load(path/'trace.npz') as f:
  q=f['qpos'][:,3:7];w,x,y,z=q.T;angles=sign*np.rad2deg(np.unwrap(np.arctan2(2*(w*z+x*y),1-2*(y*y+z*z))));angles-=angles[0]
  hits=np.flatnonzero(angles>=90.);first=None if not len(hits) else float(f['time'][hits[0]])
  assert np.isfinite(f['motor_terminal_V']).all()
  assert np.max(abs(f['motor_terminal_V']))<=3.7+1e-8
  assert report['peak_power_balance_residual_W']<1e-8
 rows.append({'side':side,'failure':report['failure'],'duration_s':report['duration_s'],'yaw_deg':report['yaw_deg'],
  'stored_5V_yaw_deg':old['yaw_deg'],'difference_from_stored_5V_deg':report['yaw_deg']-old['yaw_deg'],
  'peak_supply_current_A':report['peak_total_supply_current_A'],'maximum_signed_heading_change_deg':float(angles.max()),
  'first_90deg_time_from_sim_start_s':first,'strict_90deg_before_3s_observed':first is not None and first<3.,
  'source_sha256':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in [path/'trace.npz',path/'report.json',oldpath]}})
model=Path('software/sim/mujoco/assets/r9_fast_turn_v1')
result={'rows':rows,'runtime':{'python':platform.python_version(),'mujoco':mujoco.__version__,'numpy':np.__version__},
 'frozen_model_source_sha256':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(model.rglob('*')) if f.is_file()},
 'fixed_voltage_only':True,'latest_manufacturing_mass_included':False,'architecture_adopted':False,
 'comparison_limit':'Stored 5V reference not rerun in this experiment; small differences are not uniquely attributable to voltage without a matched runtime baseline.',
 'acceptance_complete':False}
(a.root/'summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(rows,indent=2))
