#!/usr/bin/env python3
"""Audit integrated candidate yaw grid and preservation of baseline physics limits."""
import argparse
import hashlib
import json
from pathlib import Path
import mujoco
import numpy as np
from stackchan_rl.residual import runtime_xml


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--design',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    if a.out.exists():p.error('new output required')
    path=a.design/'models/scene.xml'
    m=mujoco.MjModel.from_xml_string(runtime_xml(path))
    old=mujoco.MjModel.from_xml_string(runtime_xml(Path('assets/r8_yaw_offset_flange_v1/models/scene.xml')))
    fields=['actuator_ctrlrange','actuator_forcerange','dof_damping','dof_frictionloss','dof_armature']
    checks={name:bool(np.array_equal(getattr(m,name),getattr(old,name))) for name in fields}
    checks.update(gravity=bool(np.array_equal(m.opt.gravity,old.opt.gravity)),
                  timestep=bool(m.opt.timestep==old.opt.timestep),
                  integrator=bool(m.opt.integrator==old.opt.integrator),
                  no_equalities=bool(m.neq==0),no_exclusions=bool(m.nexclude==0),
                  parent_filter_disabled=bool(m.opt.disableflags & int(mujoco.mjtDisableBit.mjDSBL_FILTERPARENT)))
    d=mujoco.MjData(m);worst={};failed=0
    for left in np.linspace(-15,15,31):
        for right in np.linspace(-15,15,31):
            mujoco.mj_resetDataKeyframe(m,d,0)
            for side,angle in [('left',left),('right',right)]:
                d.qpos[m.joint(side+'_hip_yaw').qposadr[0]]=np.deg2rad(angle)
            mujoco.mj_forward(m,d);bad=False
            for c in d.contact:
                names=[m.geom(c.geom1).name,m.geom(c.geom2).name]
                if 'floor' in names or c.dist>=-1e-8:continue
                bad=True;key=' / '.join(sorted(names))
                if key not in worst or c.dist<worst[key]['distance_m']:
                    worst[key]={'distance_m':float(c.dist),'yaw_deg':[float(left),float(right)]}
            failed+=bad
    report={'scope':__doc__,'physics_invariants':checks,'samples':961,'failed_samples':failed,
            'worst_by_pair':worst,'limitations':['home pose only','no positive clearance margin established',
                                               'same-body CAD interfaces not certified','not a turning performance test'],
            'source_sha256':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in [Path(__file__),path]}}
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))


if __name__=='__main__':main()
