#!/usr/bin/env python3
"""Inspect generated joint-reference foot placement through model kinematics, not dynamics."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import mujoco
import numpy as np
from stackchan_rl.residual import runtime_xml

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--design',type=Path,required=True)
parser.add_argument('--reference',type=Path,required=True)
parser.add_argument('--out',type=Path,required=True)
a=parser.parse_args()
if a.out.exists():parser.error('new output required')
model=mujoco.MjModel.from_xml_string(runtime_xml(a.design/'models/scene.xml'))
data=mujoco.MjData(model)
refs=json.loads(gzip.decompress(a.reference.read_bytes()))
soles=[model.geom('col_'+side+'_sole_TPU_0').id for side in ['left','right']]
rows=[]
for sample in refs:
    base=np.array(sample['base'])
    data.qpos[:3]=base[:3,3]
    mujoco.mju_mat2Quat(data.qpos[3:7],base[:3,:3].reshape(-1))
    data.qpos[7:]=sample['q12']
    mujoco.mj_kinematics(model,data)
    rows.append([sample['time_s'],*data.geom_xpos[soles[0]],*data.geom_xpos[soles[1]],sample['segment_index']])
rows=np.array(rows);width=rows[:,2]-rows[:,5]
report={'scope':__doc__,'samples':len(rows),'width_range_mm':(np.array([width.min(),width.max()])*1000).tolist(),
        'max_20ms_foot_y_change_mm':float(np.max(abs(np.diff(rows[:,[2,5]],axis=0)))*1000),
        'segment_width_ranges_mm':{str(int(i)):(1000*np.array([width[rows[:,-1]==i].min(),width[rows[:,-1]==i].max()])).tolist() for i in np.unique(rows[:,-1])},
        'not_simulation_success_evidence':True,
        'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),a.reference,a.design/'models/scene.xml']}}
a.out.mkdir(parents=True)
np.savez_compressed(a.out/'feet.npz',values=rows,columns=['time_s','left_x','left_y','left_z','right_x','right_y','right_z','segment_index'])
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
