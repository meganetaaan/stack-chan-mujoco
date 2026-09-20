"""Read-only 70-value observation view for forward-policy transfer experiments.

No simulator stepping, root forces or new controller authority. Only the ten
original joints are exposed; the extra yaw joints retain their own servo targets.
"""
import copy
from types import SimpleNamespace
import numpy as np
from .residual_heading import HeadingResidualEnv


class LegacyPolicyView(HeadingResidualEnv):
    def __init__(self,model,data,base,qadr,vadr,reference,config,start,seed):
        # Intentionally do not construct a second physical environment.
        self.model,self.data,self.base=model,data,base
        self.qadr,self.vadr=np.asarray(qadr),np.asarray(vadr)
        if self.qadr.shape!=(10,) or self.vadr.shape!=(10,):raise ValueError('ten original joints required')
        self.reference=reference
        self.ref_q=np.array([s['q'] for s in reference])
        self.ref_support=np.array([s['support'] for s in reference])
        self.cfg=copy.deepcopy(config);self.start=np.asarray(start).copy()
        self.np_random=np.random.default_rng(seed)
        self.parameters={**config['fixed_noise'],'randomized':False}
        self.gyro_bias=self.np_random.normal(0,self.parameters['gyro_bias_std_rad_s'],3)
        self.heading_config=copy.deepcopy(config['heading_observation']);self.heading_stds=None

    def observe(self,index,filtered,previous_action):
        self.i=index;self.bank=SimpleNamespace(filtered=np.asarray(filtered).copy())
        self.previous_action=np.asarray(previous_action).copy()
        return self._observation()

    def step(self,*args,**kwargs):raise RuntimeError('observation view cannot step physics')
    def reset(self,*args,**kwargs):raise RuntimeError('construct a fresh observation view for each probe')
