"""Unvalidated, torque-limited controller for local simulation only.
No hardware writes. Motor constants are approximate, not BAM identification.
"""
from __future__ import annotations
from collections import deque
import numpy as np
from scipy.spatial.transform import Rotation
from .core import JOINT_NAMES,motor_spec,PARAMS as P
from .planner import static_torques

class ServoBank:
    def __init__(self,dt,delay_ms=None,gain_scale=1.):
        self.dt=dt
        sp=[motor_spec(n) for n in JOINT_NAMES]
        self.cap=np.array([s['simulation_torque_cap_Nm'] for s in sp])
        self.stall=np.array([s['stall_torque_Nm'] for s in sp])
        self.omega=np.array([s['no_load_speed_rpm']*np.pi/30 for s in sp])
        self.kp=np.array([s['kp_Nm_rad'] for s in sp])*gain_scale
        self.kd=np.array([s['kd_Nm_s_rad'] for s in sp])*np.sqrt(gain_scale)
        delay=P['motor']['command_delay_s'] if delay_ms is None else delay_ms/1000
        self.n_delay=int(round(delay/dt));self.queue=deque();self.last_target=None
    def command(self,q,qvel,target,ff):
        q=np.asarray(q);qvel=np.asarray(qvel);target=np.asarray(target);ff=np.asarray(ff)
        if self.last_target is None:self.last_target=target.copy()
        target_vel=(target-self.last_target)/self.dt;self.last_target=target.copy()
        self.queue.append((target.copy(),np.clip(target_vel,-2.,2.),ff.copy()))
        if len(self.queue)>self.n_delay+1:self.queue.popleft()
        delayed,dvel,dff=self.queue[0]
        raw=self.kp*(delayed-q)+self.kd*(dvel-qvel)+dff
        # Approximate linear DC torque-speed envelope only in motoring direction.
        # Braking is capped too; electrical regeneration/heat NOT modelled.
        motoring=(raw*qvel)>0
        available=np.where(motoring,self.stall*np.maximum(0,1-np.abs(qvel)/self.omega),self.stall)
        bound=np.minimum(self.cap,available)
        torque=np.clip(raw,-bound,bound)
        return torque,abs(raw)>bound+1e-9,bound


def posture_target(reference,actual_base,gyro,enabled=True):
    """Small bounded tilt correction, untuned on this mechanism.
    This acts only on joint targets, never on floating-base pose/force.
    """
    q=reference.q.copy()
    if enabled:
        roll,pitch,_=Rotation.from_matrix(actual_base[:3,:3]).as_euler('xyz')
        corr=np.clip(.20*np.array([roll,pitch])+.015*np.asarray(gyro)[:2],-.06,.06)
        for i,w in enumerate(reference.support):
            q[5*i+3]+=w*corr[1]
            q[5*i+4]+=w*corr[0]
    limits=np.tile(np.array([P['joint_limits_rad'][n] for n in ['hip_roll','hip_pitch','knee','ankle_pitch','ankle_roll']]),(2,1))
    return np.clip(q,limits[:,0]+1e-5,limits[:,1]-1e-5)
