"""Evaluate solver completion and artificial anchor reactions of a pressure probe."""
import argparse,json,re
from pathlib import Path
import numpy as np
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True);a=p.parse_args()
plan=json.loads((a.run/'plan.json').read_text());run=json.loads((a.run/'run.json').read_text())
text=(a.run/'contact.dat').read_text()
def number(s):return float(re.sub(r'^([+-]?(?:\d+\.?\d*|\.\d+))([+-]\d{3})$',r'\1e\2',s.replace('D','E')))
rows=[]
for time,body in re.findall(r'(?<!total )forces \(fx,fy,fz\) for set ANCHORS and time\s+(\S+)\s*\n\s*\n(.*?)(?=\n\s*\n)',text,re.S):
 forces={int(v[0]):np.array([number(x) for x in v[1:]]) for line in body.splitlines() if (v:=line.split())}
 total=sum(forces.values(),np.zeros(3)); moment=np.zeros(3)
 for anchors in plan['anchors'].values():
  for anchor in anchors:moment+=np.cross(anchor['xyz'],forces[anchor['node']])
 scale=4*plan['force_per_corner_N']*number(time)
 rows.append({'time':number(time),'total_anchor_force_N':total.tolist(),'anchor_moment_Nmm':moment.tolist(),
  'largest_anchor_force_N':float(max(np.linalg.norm(f) for f in forces.values())),
  'relative_total_anchor_force':float(np.linalg.norm(total)/scale)})
complete=bool(rows and abs(rows[-1]['time']-1)<1e-7 and run['solver_finished'])
gates={'solver_completion':complete,'anchor_force':bool(complete and all(r['relative_total_anchor_force']<=plan['criteria']['relative_total_anchor_force_max'] for r in rows))}
report={'scope':__doc__,'increments':rows,'gates':gates,'passed':all(gates.values()),
 'joint_strength_verified':False,'actual_screw_preload_verified':False,
 'limitations':plan['limitations']+['small total anchor force alone does not rule out a self-equilibrated restraint effect; individual reactions and moments retained for review']}
(a.run/'evaluation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
