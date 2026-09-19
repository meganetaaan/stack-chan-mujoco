"""Candidate yaw-before-roll leg kinematics; no physical success implied.

Wrap the original five-axis geometry without scaling or length changes. The yaw
axis is a caller-supplied design candidate, not an asserted motor shaft location.
Collision, mounts and inertias must be resolved separately before acceptance.
"""
import numpy as np


def rz(angle):
    c,s=np.cos(angle),np.sin(angle)
    return np.array([[c,-s,0.],[s,c,0.],[0.,0.,1.]])


class YawLegKinematics:
    def __init__(self, legacy, axis_base_m, yaw_limits_rad=(-.2,.2)):
        self.legacy=legacy
        self.axes={side:np.asarray(axis_base_m[side],dtype=float) for side in ('left','right')}
        self.limits=np.asarray(yaw_limits_rad,dtype=float)
        if any(a.shape!=(3,) or not np.isfinite(a).all() for a in self.axes.values()):
            raise ValueError('finite 3D axis point for each side required')
        if self.limits.shape!=(2,) or not np.isfinite(self.limits).all() or not self.limits[0]<0<self.limits[1]:
            raise ValueError('finite yaw limits must straddle zero')

    def rotated_legacy_base(self,yaw,side,base):
        base=np.asarray(base,dtype=float)
        if base.shape!=(4,4) or not np.isfinite(base).all() or not np.isfinite(yaw):
            raise ValueError('finite homogeneous base transform and yaw required')
        pivot=self.axes[side]
        transform=np.eye(4);transform[:3,:3]=rz(yaw)
        transform[:3,3]=pivot-rz(yaw)@pivot
        return base@transform

    def fk_leg(self,q,side='left',base=None):
        q=np.asarray(q,dtype=float)
        if q.shape!=(6,) or not np.isfinite(q).all():raise ValueError('six finite joint angles required')
        base=np.eye(4) if base is None else np.asarray(base,dtype=float)
        transformed=self.rotated_legacy_base(q[0],side,base)
        frames,sole,positions,axes=self.legacy.fk_leg(q[1:],side,transformed)
        yaw_frame=base.copy()
        yaw_frame[:3,3]=(base@np.r_[self.axes[side],1.])[:3]
        yaw_frame[:3,:3]=base[:3,:3]@rz(q[0])
        return ([yaw_frame,*frames],sole,
                np.vstack([yaw_frame[:3,3],positions]),
                np.vstack([base[:3,:3]@np.array([0.,0.,1.]),axes]))

    def solve_flat_foot(self,target_xyz,target_yaw,side,base,seed=None):
        base=np.asarray(base,dtype=float)
        target_xyz=np.asarray(target_xyz,dtype=float)
        if base.shape!=(4,4) or target_xyz.shape!=(3,) or not np.isfinite(base).all() or not np.isfinite(target_xyz).all() or not np.isfinite(target_yaw):
            raise ValueError('finite base, foot position and heading required')
        body_yaw=np.arctan2(base[1,0],base[0,0])
        if not np.allclose(base[:3,:3],rz(body_yaw),atol=1e-10,rtol=0):
            raise ValueError('analytic candidate IK requires an upright body')
        yaw=np.arctan2(np.sin(target_yaw-body_yaw),np.cos(target_yaw-body_yaw))
        if not self.limits[0]<=yaw<=self.limits[1]:raise ValueError('candidate yaw limit exceeded')
        transformed=self.rotated_legacy_base(yaw,side,base)
        local=transformed[:3,:3].T@(target_xyz-transformed[:3,3])
        old_seed=None if seed is None else np.asarray(seed,dtype=float)[1:]
        q,error,diagnostic=self.legacy.solve_leg(local,side,np.eye(4),old_seed,np.eye(3))
        return np.r_[yaw,q],error,diagnostic
