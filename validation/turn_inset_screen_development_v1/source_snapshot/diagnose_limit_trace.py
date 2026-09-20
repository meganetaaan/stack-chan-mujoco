"""Identify recorded joint limit violations using model joint addresses."""
import argparse
import hashlib
import json
from pathlib import Path
import mujoco
import numpy as np

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--source', type=Path, required=True)
p.add_argument('--model', type=Path, required=True)
p.add_argument('--out', type=Path, required=True)
a=p.parse_args()
model=mujoco.MjModel.from_xml_path(str((a.model/'models/scene.xml').resolve()))
report=json.loads((a.source/'report.json').read_text())
with np.load(a.source/'trace.npz') as trace:
    finite=all(np.isfinite(trace[k]).all() for k in trace.files)
    rows=[]
    for name in report['joint_names']:
        j=model.joint(name);q=trace['qpos'][:,int(j.qposadr[0])]
        margin=np.minimum(q-j.range[0],j.range[1]-q)
        i=int(np.argmin(margin));violations=np.flatnonzero(margin < -1e-5)
        rows.append(dict(joint=name,minimum_margin_rad=float(margin[i]),time_s=float(trace['time'][i]),
                         angle_rad=float(q[i]),limits_rad=j.range.tolist(),
                         first_violation_s=float(trace['time'][violations[0]]) if len(violations) else None))
result=dict(finite_trace=finite,guard_tolerance_rad=1e-5,joints=rows,
            source_sha256={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in (a.source/'trace.npz',a.model/'models/scene.xml')})
a.out.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps([r for r in rows if r['first_violation_s'] is not None]))
