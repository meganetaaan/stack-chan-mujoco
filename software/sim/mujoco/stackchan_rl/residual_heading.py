"""R6 residual v2: expose noisy, externally referenced heading and lateral pose.

This is an explicit state-estimation assumption for simulation. It is NOT an
IMU-only yaw estimator; hardware needs an external heading/position reference.
The parent physics, actuation, limits and protective criteria remain unchanged.
"""
import copy
import numpy as np
import gymnasium as gym
from .residual import ResidualEnv,OBS_FIELDS,ROOT,sha


class HeadingResidualEnv(ResidualEnv):
    def __init__(self,config,**kwargs):
        if config['schema']!='r6-residual-heading-v2':raise ValueError('requires heading-v2 configuration')
        base_config=copy.deepcopy(config);base_config['schema']='r6-residual-v1'
        super().__init__(base_config,**kwargs)
        self.heading_config=copy.deepcopy(config['heading_observation'])
        self.observation_space=gym.spaces.Box(-np.inf,np.inf,(70,),np.float32)
        self.fingerprint['schema']=config['schema']
        self.fingerprint['source_sha256']['stackchan_rl/residual_heading.py']=sha(ROOT/'stackchan_rl/residual_heading.py')
        self.fingerprint['observation_fields']=OBS_FIELDS+[
            ('noisy_external_heading_sin_cos',2),('noisy_lateral_error',1),('world_velocity_xy',2)]
        self.fingerprint['heading_state_estimation']='external_reference_plus_white_noise; not IMU-only'
        self.fingerprint['control_parameters']={k:config[k] for k in ('command_m_s','policy_dt_s',
            'residual_scale_rad','slew_rad_s','lowpass_s','protection','heading_observation')}

    def reset(self,**kwargs):
        self.heading_stds=None
        return super().reset(**kwargs)

    def _observation(self):
        obs=super()._observation()
        if self.heading_stds is None:
            cfg=self.heading_config
            self.heading_stds=([float(self.np_random.uniform(*cfg[k])) for k in
                ('heading_std_rad_range','lateral_std_m_range')] if self.parameters['randomized'] else
                [cfg['fixed_heading_std_rad'],cfg['fixed_lateral_std_m']])
            self.parameters.update(external_heading_std_rad=self.heading_stds[0],
                                   lateral_pose_std_m=self.heading_stds[1],
                                   heading_source='simulated external reference; not IMU-only')
        rot=self.data.xmat[self.base].reshape(3,3)
        yaw=np.arctan2(rot[1,0],rot[0,0])+self.np_random.normal(0,self.heading_stds[0])
        lateral=self.data.xpos[self.base,1]-self.start[1]+self.np_random.normal(0,self.heading_stds[1])
        # Existing body velocity is privileged state estimation; make the
        # episode/world frame explicit rather than silently equating the two.
        world_velocity=(rot@obs[36:39])[:2]
        return np.concatenate((obs,[np.sin(yaw),np.cos(yaw),lateral],world_velocity)).astype(np.float32)

    def step(self,action):
        obs,reward,terminated,truncated,info=super().step(action)
        rot=self.data.xmat[self.base].reshape(3,3)
        yaw=float(np.arctan2(rot[1,0],rot[0,0]));lateral=float(self.data.xpos[self.base,1]-self.start[1])
        penalty=5.*(1.-np.cos(yaw))+.2*min((lateral/.1)**2,10.)
        reward-=float(penalty)
        info.update(heading_error_rad=yaw,lateral_error_m=lateral,direction_penalty=float(penalty))
        return obs,reward,terminated,truncated,info
