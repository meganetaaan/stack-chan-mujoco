"""Lateral velocity adapter; existing (vx, yaw rate) interface stays compatible."""
import numpy as np


def crab_keyboard(keys):
    if 'SPACE' in keys:return np.zeros(3)
    f=int('W' in keys)-int('S' in keys)
    return np.array([(.015 if f>0 else .008)*f,
                     .004*(int('A' in keys)-int('D' in keys)),0.])


class LateralControl:
    def __init__(self):
        self.request=0.;self.target=0.;self.drive=0.;self.integral=0.

    def update(self,request,measured,ready,scale=1.):
        if not np.isfinite(request):raise ValueError('finite lateral velocity required')
        self.request=float(request)
        goal=float(np.clip(request,-.004,.004))*scale if ready else 0.
        self.target+=float(np.clip(goal-self.target,-.0002,.0002))
        error=self.target-measured
        if abs(self.target)<1e-9:
            self.target=0.;self.drive=0.;self.integral=0.
        else:
            self.integral=float(np.clip(self.integral+.008*error,-.002,.002))
            raw=self.target+.1*error+self.integral
            self.drive=float(np.sign(self.target)*np.clip(raw*np.sign(self.target),0,.006))
        return self.drive
