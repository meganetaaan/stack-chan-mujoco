"""Define the joint envelope over both turn signs and forward/backward motions."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import numpy as np


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--turns',type=Path,required=True);p.add_argument('--translation',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    if a.out.exists():p.error('new output required')
    a.out.mkdir(parents=True)
    for folder in [a.turns,a.translation]:
        for path in folder.glob('*.npz'):shutil.copyfile(path,a.out/path.name)
    contract=json.loads((a.turns/'requirements.json').read_text())
    arrays=[]
    for path in sorted(a.out.glob('*.npz')):
        with np.load(path) as data:arrays.append((path.name,data['time'],data['q_rad'],data['torque_Nm']))
    for j,req in enumerate(contract['joint_requirements']):
        req['required_motion_rad']=[min(float(q[:,j].min()) for _,_,q,_ in arrays),max(float(q[:,j].max()) for _,_,q,_ in arrays)]
        winner=max(arrays,key=lambda r:float(np.max(abs(r[3][:,j]))));name,t,q,tau=winner
        i=int(np.argmax(abs(tau[:,j])));req['external_fixture_load_Nm']=float(-tau[i,j])
        req['source_peak_time_s']=float(t[i]);req['source_peak_file']=name
    contract['source_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in a.out.glob('*.npz')}
    contract['scope']=__doc__;contract['command_speeds_m_s']={'forward':.04,'backward':-.02}
    (a.out/'requirements.json').write_text(json.dumps(contract,indent=2)+'\n')
    print(json.dumps({'files':list(contract['source_sha256']),'joints':len(contract['joint_requirements'])}))


if __name__=='__main__':main()
