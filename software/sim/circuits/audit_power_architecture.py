"""Desk comparison of supply segmentation; no hardware qualification or new simulation."""
import json, hashlib
from pathlib import Path
import numpy as np
root=Path('validation/power_architecture_decision_v1')
rows=[]
for side in ['left','right']:
 p=Path(f'validation/prototype_epic4_v1/load_export_{side}_v1')
 meta=json.loads((p/'schema.json').read_text());d=np.load(p/'loads.npz')
 for leg in ['left','right']:
  ids=[i for i,n in enumerate(meta['joint_names']) if n.startswith(leg+'_')]
  assert len(ids)==6
  currents=d['supply_current_A'][:,ids]
  draw=np.maximum(currents,0).sum(axis=1);regen=np.maximum(-currents,0).sum(axis=1)
  rows.append({'turn':side,'leg':leg,'peak_draw_A':float(draw.max()),'peak_regeneration_A':float(regen.max()),'peak_net_draw_A':float(currents.sum(axis=1).max()),'source_sha256':hashlib.sha256((p/'loads.npz').read_bytes()).hexdigest()})
report={'scope':'Two frozen full-body turn traces only; not all motions or hardware maxima','rows':rows,'motor_limit_sum_A':6*(.735+.870),'per_leg_motor_limit_sum_A':3*(.735+.870),'voltage_budget':{'source_min_V':5*.97,'normal_load_min_V':4.75,'remaining_drop_V':5*.97-4.75,'per_leg_loop_resistance_ceiling_at_motor_sum_ohm':(5*.97-4.75)/(3*(.735+.870))},'limitations':['Motor current sum is not DC supply peak or hardware protection guarantee','Resistance ceiling leaves no allowance for ripple, dynamic droop, idle or auxiliary currents; necessary screening only','Current traces use existing approximate motor and ideal bridge model','Split outputs must not be connected together by servo power cables','Regeneration must be handled on each isolated output rail'],'qualified':False}
(root/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
