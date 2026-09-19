"""Supplement CAD subset inspection with all same-base collision proxies."""
import hashlib,json
from pathlib import Path
import mujoco
from stackchan_rl.residual import runtime_xml
p=Path('assets/r8_yaw_offset_flange_v1')
m=mujoco.MjModel.from_xml_string(runtime_xml(p/'models/scene.xml'));d=mujoco.MjData(m)
mujoco.mj_resetDataKeyframe(m,d,0);mujoco.mj_forward(m,d)
rows=[]
for side in ['left','right']:
 i=m.geom('col_'+side+'_yaw_motor_case').id
 for j in range(m.ngeom):
  if i==j or m.geom_bodyid[j]!=m.body('base').id:continue
  if not (m.geom_contype[j] or m.geom_conaffinity[j]):continue
  dist=mujoco.mj_geomDistance(m,d,i,j,1.,None)
  rows.append({'case':m.geom(i).name,'other':m.geom(j).name,'distance_m':float(dist)})
r={'scope':__doc__,'minimum_m':min(x['distance_m'] for x in rows),
   'penetrations':[x for x in rows if x['distance_m']< -1e-8],'pairs':rows,
   'scene_sha256':hashlib.sha256((p/'models/scene.xml').read_bytes()).hexdigest(),
   'limitations':'analytic/convex collision proxies, not detailed CAD or attachment validation'}
print(json.dumps(r,indent=2))
