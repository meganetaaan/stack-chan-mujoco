"""Delayed noisy attitude-estimator output for controller development.

Gravity is an estimated direction, not a raw accelerometer signal. A hardware
filter and its acceleration rejection still require identification. No global
heading, position, translational velocity or contact force is exposed here.
"""
from collections import deque
import numpy as np
import mujoco


class AttitudeObserver:
    def __init__(self,model,data,base,parameters,seed,dt=.02,delay_s=.02):
        if not np.isfinite([dt,delay_s]).all() or dt<=0 or not 0<=delay_s<=.1:raise ValueError('invalid sampling or delay')
        self.model,self.data,self.base=model,data,base
        self.rng=np.random.default_rng(seed)
        self.gravity_std=parameters['gravity_noise_std'];self.gyro_std=parameters['gyro_noise_std_rad_s']
        self.bias=self.rng.normal(0,parameters['gyro_bias_std_rad_s'],3)
        self.ticks=int(round(delay_s/dt));self.dt=dt;self.seed=seed
        first=self._measure();self.history=deque([first.copy() for _ in range(self.ticks+1)],maxlen=self.ticks+1)

    def _measure(self):
        rot=self.data.xmat[self.base].reshape(3,3)
        gravity=-rot[2]+self.rng.normal(0,self.gravity_std,3);gravity/=np.linalg.norm(gravity)
        velocity=np.zeros(6)
        mujoco.mj_objectVelocity(self.model,self.data,mujoco.mjtObj.mjOBJ_BODY,self.base,velocity,1)
        return np.r_[gravity,velocity[:3]+self.bias+self.rng.normal(0,self.gyro_std,3)]

    def read(self):
        self.history.append(self._measure())
        return self.history[0].copy()

    def metadata(self):
        return {'source':__doc__,'sample_dt_s':self.dt,'effective_delay_s':self.ticks*self.dt,
                'gravity_noise_std':self.gravity_std,'gyro_noise_std_rad_s':self.gyro_std,
                'gyro_bias_rad_s':self.bias.tolist(),'seed':self.seed}
