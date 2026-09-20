"""Body-heading velocity commands and bounded, cycle-averaged feedback."""
from collections import deque
import numpy as np


def keyboard_velocity(keys):
    if 'SPACE' in keys:return np.zeros(2)
    forward=int('W' in keys)-int('S' in keys)
    return np.array([(.025 if forward>0 else .012)*forward,
                     np.deg2rad(32)*(int('A' in keys)-int('D' in keys))])


def limit_velocity(value):
    value=np.asarray(value,dtype=float)
    if value.shape!=(2,) or not np.isfinite(value).all():raise ValueError('two finite velocity values required')
    v,w=value
    # Separate combined-motion envelope: full turn travel is reserved for pivoting.
    v=float(np.clip(v,-.012,.025))
    yaw_cap=np.deg2rad(32) if abs(v)<1e-8 else np.deg2rad(12)
    w=float(np.clip(w,-yaw_cap,yaw_cap))
    return np.array([v,w])


class VelocityControl:
    def __init__(self,dt=.02):
        self.dt=dt;self.history=deque(maxlen=40)
        self.request=np.zeros(2);self.target=np.zeros(2);self.measured=np.zeros(2)
        self.drive=np.zeros(2);self.integral=np.zeros(2);self.lateral=0.
        self.feedback=True;self.reason='';self.steady_time=np.zeros(2)
        self.safety_scale=1.;self.no_contact_s=0.

    def observe(self,velocity):
        self.history.append(np.asarray(velocity).copy())
        avg=np.mean(self.history,axis=0)
        self.measured=avg[[0,2]];self.lateral=float(avg[1])

    def observe_support(self,tilt_deg,loads):
        self.no_contact_s=self.no_contact_s+self.dt if max(loads)<.35 else 0.
        self.safety_scale=float(np.clip((14.-tilt_deg)/4.,0.,1.))
        if self.no_contact_s>.1:self.safety_scale=0.

    def update(self,request,ready=True):
        self.request=np.asarray(request,dtype=float).copy()
        limited=limit_velocity(self.request)
        self.reason='envelope' if not np.allclose(limited,self.request) else ''
        if self.safety_scale<1:
            limited*=self.safety_scale;self.reason='posture/contact limit'
        if not ready:limited[:]=0
        # Slew targets; step references themselves are latched at touchdown.
        previous=self.target.copy()
        self.target+=np.clip(limited-self.target,-np.array([.04,.8])*self.dt,np.array([.04,.8])*self.dt)
        self.steady_time=np.where(abs(previous-self.target)<1e-8,self.steady_time+self.dt,0.)
        error=self.target-self.measured
        active=abs(self.target)>1e-7
        previous_integral=self.integral.copy()
        if self.feedback:
            delta=error*self.dt*np.array([.4,.4])*(self.steady_time>=.8)
            self.integral=np.clip(self.integral+delta,[-.008,-.12],[.008,.12])
            self.integral[~active]=0
            correction=error*np.array([.15,.20])+self.integral
        else:correction=np.zeros(2)
        raw=self.target+correction
        # Never reverse an axis to correct overshoot or move after release.
        raw=np.where(active,np.sign(self.target)*np.maximum(0,raw*np.sign(self.target)),0)
        bound=np.array([.04 if raw[0]>=0 else .022,np.deg2rad(40) if abs(raw[0])<1e-8 else np.deg2rad(16)])
        self.drive=np.clip(raw,-bound,bound)
        saturated=abs(raw-self.drive)>1e-10
        self.integral[saturated]=previous_integral[saturated]
        if saturated.any():self.reason='feedback limit'
        return self.drive.copy()
