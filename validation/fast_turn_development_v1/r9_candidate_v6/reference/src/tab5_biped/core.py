"""Single source of link/joint coordinates. SI units throughout this module."""
from __future__ import annotations
from pathlib import Path
import json
import numpy as np
from scipy.spatial.transform import Rotation
from scipy.optimize import least_squares

ROOT=Path(__file__).resolve().parents[2]
PARAMS=json.loads((ROOT/'robot.json').read_text())
KIN=PARAMS['kinematics']
JOINT_TYPES=('hip_roll','hip_pitch','knee','ankle_pitch','ankle_roll')
SIDES=('left','right')
JOINT_NAMES=[f'{s}_{j}' for s in SIDES for j in JOINT_TYPES]
AXES=np.array([[1,0,0],[0,1,0],[0,1,0],[0,1,0],[1,0,0]],float)
LIMITS=np.array([PARAMS['joint_limits_rad'][j] for j in JOINT_TYPES])

def transform(xyz=(0,0,0),R=None):
    T=np.eye(4); T[:3,3]=xyz
    if R is not None:T[:3,:3]=R
    return T

def origins(side):
    sign=1 if side=='left' else -1
    return np.array([[KIN.get('hip_roll_x_mm',0),sign*KIN['hip_half_spacing_mm'],KIN['hip_roll_height_mm']],KIN['hip_pitch_offset_mm'],[0,0,-KIN['thigh_mm']],[0,sign*KIN.get('shin_outset_y_mm',0),-KIN['shin_mm']],KIN['ankle_roll_offset_mm']],float)/1000

def sole_offset(side):
    sign=1 if side=='left' else -1
    return np.array([KIN.get('foot_center_x_mm',0),sign*KIN.get('foot_outset_y_mm',0),-KIN['sole_drop_mm']],float)/1000

def fk_leg(q,side='left',base=None):
    """Five serial hinges; returned frames are after each joint rotation."""
    q=np.asarray(q,float)
    if q.shape!=(5,):raise ValueError('Each leg requires exactly five angles')
    T=np.eye(4) if base is None else np.array(base,copy=True)
    frames=[]; axis_pos=[]; axis_world=[]
    for a,p,axis in zip(q,origins(side),AXES):
        T=T@transform(p)
        axis_pos.append(T[:3,3].copy());axis_world.append(T[:3,:3]@axis)
        T=T@transform(R=Rotation.from_rotvec(a*axis).as_matrix())
        frames.append(T.copy())
    sole=T@transform(sole_offset(side))
    return frames,sole,np.array(axis_pos),np.array(axis_world)

def all_frames(q,base=None):
    q=np.asarray(q)
    if q.shape!=(10,):raise ValueError('Expected ten joint angles')
    base=np.eye(4) if base is None else base
    out={'base':base.copy()}
    for i,s in enumerate(SIDES):
        fs,_,_,_=fk_leg(q[5*i:5*i+5],s,base)
        out.update({f'{s}_{j}':T for j,T in zip(JOINT_TYPES,fs)})
    return out

def nominal():
    k=PARAMS['gait']['nominal_knee_rad']
    q=np.tile([0,-k/2,k,-k/2,0],2).astype(float)
    _,sole,_,_=fk_leg(q[:5])
    base=np.eye(4);base[2,3]=-sole[2,3]
    return q,base

def solve_leg(target_xyz,side,base,seed=None,target_R=None):
    """Numerical constrained IK; five DOFs cannot command arbitrary 6D poses.
    Targets here use flat feet, zero yaw, and an upright body.
    """
    if seed is None:seed=nominal()[0][:5]
    target_R=np.eye(3) if target_R is None else target_R
    # Closed form for the supported upright-body / flat-foot task.
    if np.allclose(base[:3,:3],np.eye(3),atol=1e-10) and np.allclose(target_R,np.eye(3),atol=1e-10):
        o=origins(side)
        v=np.asarray(target_xyz)-sole_offset(side)-(base[:3,3]+o[0])
        roll=np.arctan2(v[1],-v[2])-np.arcsin(np.clip(np.sum(o[1:,1])/np.hypot(v[1],v[2]),-1,1))
        v=Rotation.from_rotvec([-roll,0,0]).apply(v)-o[1]-o[4]
        L1,L2=KIN['thigh_mm']/1000,KIN['shin_mm']/1000
        c=(v[0]**2+v[2]**2-L1**2-L2**2)/(2*L1*L2)
        if c < -1-1e-8 or c > 1+1e-8:raise ValueError('Unreachable analytic leg target')
        knee=np.sign(PARAMS['gait']['nominal_knee_rad'])*np.arccos(np.clip(c,-1,1))
        pitch=np.arctan2(-v[0],-v[2])-np.arctan2(L2*np.sin(knee),L1+L2*np.cos(knee))
        q=np.array([roll,pitch,knee,-pitch-knee,-roll])
        if np.any(q<LIMITS[:,0]-1e-8) or np.any(q>LIMITS[:,1]+1e-8):raise ValueError('Analytic IK exceeds configured joint limits')
        _,T,_,_=fk_leg(q,side,base)
        return q,float(np.linalg.norm(T[:3,3]-target_xyz)),float(np.linalg.norm(Rotation.from_matrix(target_R.T@T[:3,:3]).as_rotvec()))
    def residual(q):
        _,T,_,_=fk_leg(q,side,base)
        r=Rotation.from_matrix(target_R.T@T[:3,:3]).as_rotvec()
        return np.r_[T[:3,3]-target_xyz,0.06*r]
    result=least_squares(residual,np.clip(seed,LIMITS[:,0]+1e-9,LIMITS[:,1]-1e-9),bounds=(LIMITS[:,0],LIMITS[:,1]),ftol=1e-11,xtol=1e-11,gtol=1e-11,max_nfev=70)
    _,T,_,_=fk_leg(result.x,side,base)
    err=float(np.linalg.norm(T[:3,3]-target_xyz))
    ang=float(np.linalg.norm(Rotation.from_matrix(target_R.T@T[:3,:3]).as_rotvec()))
    if err>0.0004 or ang>0.008:
        raise ValueError(f'Unreachable {side} target: {err*1000:.3f} mm, {ang:.4f} rad')
    return result.x,err,ang

def jacobian(q,side,base,point=None):
    fs,sole,ps,axs=fk_leg(q,side,base)
    point=sole[:3,3] if point is None else np.asarray(point)
    return np.vstack([np.cross(axs,point-ps).T,axs.T])

def smooth(u):
    u=float(np.clip(u,0,1));return u*u*u*(10+u*(-15+6*u))


def motor_spec(joint_name):
    spec=dict(PARAMS["motor"])
    over=PARAMS.get("motor_overrides",{})
    if any(joint_name.endswith("_"+j) or joint_name==j for j in over.get("joint_types",[])):
        spec.update(over)
    return spec
