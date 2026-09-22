"""Evaluate predeclared posture cases without changing joint or yaw gates."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np,mujoco
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);a=p.parse_args();root=Path(__file__).resolve().parents[3];plan=json.loads((a.source/'plan.json').read_text());model=root/'software/sim/mujoco/assets/r9_fast_turn_v1/models/scene.xml';m=mujoco.MjModel.from_xml_path(str(model));rows=[]
for inset in plan['inset_mm']:
 folder=a.source/f'inset{inset}';r=json.loads((folder/'report.json').read_text());margins=[]
 with np.load(folder/'trace.npz') as t:
  for name in r['joint_names']:
   j=m.joint(name);q=t['qpos'][:,int(j.qposadr[0])];margin=np.minimum(q-j.range[0],j.range[1]-q);idx=int(margin.argmin());margins.append({'joint':name,'minimum_margin_rad':float(margin[idx]),'time_s':float(t['time'][idx])})
 gates={'no_failure':r['failure'] is None,'duration':r['duration_s']>=plan['criteria']['duration_s']-1e-9,'yaw':abs(r['yaw_deg']-90)<=plan['criteria']['yaw_error_deg']};rows.append({'inset_mm':inset,'duration_s':r['duration_s'],'yaw_deg':r['yaw_deg'],'gates':gates,'margins':margins,'trace_sha256':hashlib.sha256((folder/'trace.npz').read_bytes()).hexdigest()})
out={'cases':rows,'mechanical_design_verified':False};(a.source/'evaluation.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps([{'inset':r['inset_mm'],'yaw':r['yaw_deg'],'gates':r['gates'],'worst_margin':min(r['margins'],key=lambda x:x['minimum_margin_rad'])} for r in rows],indent=2))
