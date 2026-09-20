"""Interface loads from MuJoCo: parent-on-child wrench at the joint origin.

MuJoCo cfrc_int is world-aligned, at the kinematic subtree COM, in
[torque, force] order. Shift the origin, then rotate both components.
"""
import numpy as np
import mujoco


def joint_wrenches(model,data,names):
    mujoco.mj_rnePostConstraint(model,data)
    result=[]
    for name in names:
        joint=model.joint(name);body=int(joint.bodyid[0]);root=int(model.body_rootid[body])
        c=data.cfrc_int[body];force=c[3:]
        origin=data.xanchor[joint.id]
        moment=c[:3]+np.cross(data.subtree_com[root]-origin,force)
        rotation=data.xmat[body].reshape(3,3)
        result.append(np.r_[rotation.T@force,rotation.T@moment])
    return np.array(result)


def circuit_load(trace):
    """Return demanded DC draw and available regeneration separately, amperes."""
    currents=np.asarray(trace['supply_current_A'])
    if currents.ndim!=2 or not np.isfinite(currents).all():raise ValueError('finite [time,joint] currents required')
    return {'draw_A':np.maximum(currents,0).sum(axis=1),
            'regeneration_A':np.maximum(-currents,0).sum(axis=1),
            'net_A':currents.sum(axis=1)}


def structural_load(trace):
    """Return simultaneous joint-local wrenches; never mix unrelated maxima."""
    wrench=np.asarray(trace['joint_wrench_local_force_moment'])
    if wrench.ndim!=3 or wrench.shape[2]!=6 or not np.isfinite(wrench).all():raise ValueError('finite [time,joint,6] wrenches required')
    return wrench
