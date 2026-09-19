#!/usr/bin/env python3
"""Sample yaw limits in the home pose; this is not a full CAD or motion audit."""
import argparse
import hashlib
import json
from pathlib import Path
import mujoco
import numpy as np
from stackchan_rl.residual import runtime_xml


def audit(design, samples=19):
    scene=design/'models/scene.xml'
    model=mujoco.MjModel.from_xml_string(runtime_xml(scene))
    data=mujoco.MjData(model)
    worst={};home=[];failed=0
    for left in np.linspace(-.09,.09,samples):
        for right in np.linspace(-.09,.09,samples):
            mujoco.mj_resetDataKeyframe(model,data,0)
            for side,value in [('left',left),('right',right)]:
                data.qpos[model.joint(side+'_hip_yaw').qposadr[0]]=value
            mujoco.mj_forward(model,data)
            bad=[]
            for contact in data.contact:
                names=[model.geom(contact.geom1).name,model.geom(contact.geom2).name]
                if 'floor' in names or contact.dist>=-1e-8:continue
                key=' / '.join(sorted(names));bad.append(key)
                if key not in worst or contact.dist<worst[key]['distance_m']:
                    worst[key]={'distance_m':float(contact.dist),'yaw_rad':[float(left),float(right)]}
            failed+=bool(bad)
            if abs(left)<1e-12 and abs(right)<1e-12:home=bad
    return {'scope':__doc__,'design':str(design),'samples':samples*samples,
            'failed_samples':failed,'home_penetrations':home,'worst_by_pair':worst,
            'yaw_mount_penetration_pairs':[key for key in worst if 'yaw_' in key],
            'mass_kg':float(model.body_mass.sum()),
            'parent_filter_disabled':bool(model.opt.disableflags & int(mujoco.mjtDisableBit.mjDSBL_FILTERPARENT)),
            'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [scene,Path(__file__)]},
            'limitations':['same-body interference requires CAD inspection','home leg pose only',
                           'discrete yaw grid, not continuous swept-volume proof',
                           'fastener attachment and strength not validated']}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--design',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    if args.out.exists():parser.error('new output required')
    report=audit(args.design)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['samples','failed_samples','home_penetrations','yaw_mount_penetration_pairs','mass_kg']}))
