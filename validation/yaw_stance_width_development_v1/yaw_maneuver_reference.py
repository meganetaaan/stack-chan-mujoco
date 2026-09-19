"""Continuous command-driven stepping with finite hip-yaw heading references.

The virtual heading is used only for leg IK. It never sets the simulated root.
Commands are latched at step boundaries so a foot is not reset while planted.
"""
from types import SimpleNamespace
import numpy as np
from maneuver_reference import CommandReference


class YawCommandReference(CommandReference):
    def __init__(self, initial, pose, smooth, protocol, kinematics, shift_fraction=.35, steady_inset_mm=25.5, step_period=.32, forward_period=None, swing_profile="quartic"):
        if not np.isfinite(shift_fraction) or not .2<=shift_fraction<=.5:raise ValueError('shift fraction outside [.2,.5]')
        if not np.isfinite(steady_inset_mm) or not 20<=steady_inset_mm<26:raise ValueError('steady inset outside [20,26) mm')
        if not np.isfinite(step_period) or not .24<=step_period<=.4:raise ValueError('step period outside [.24,.4] seconds')
        if swing_profile not in ("quartic","c2"):raise ValueError("unknown swing profile")
        self.swing_profile=swing_profile
        self.shift_fraction=shift_fraction
        self.steady_inset_delta=(steady_inset_mm-24.)/1000
        self.step_period=step_period
        self.forward_period=step_period if forward_period is None else forward_period
        if not np.isfinite(self.forward_period) or not .24<=self.forward_period<=.4:raise ValueError('forward period outside [.24,.4] seconds')
        self.kinematics=kinematics
        self.heading=0.
        self.foot_headings=np.zeros(2)
        super().__init__(initial,pose,smooth,protocol)

    def begin(self,t):
        # Finish the prior heading segment before selecting the next command.
        self.motion_steps=(getattr(self,'motion_steps',0)+1) if getattr(self,'mode',None)=='step' else 0
        if hasattr(self,'start'):
            self.heading,self.foot_headings=self.heading_geometry(t)
        super().begin(t)
        index=min(np.searchsorted(self.boundaries,t+1e-9,side='right')-1,len(self.protocol['segments'])-1)
        command=self.protocol['segments'][index]
        if command['vx_m_s']==0 and command['yaw_rate_rad_s']==0 and np.max(abs(self.foot_headings-self.heading))>1e-9:
            self.mode='align'
            self.swing=1-self.stance
        self.yaw_rate=command['yaw_rate_rad_s'] if self.mode=='step' else 0.
        self.from_heading=self.heading
        self.from_foot_headings=self.foot_headings.copy()
        if self.mode in ('step','align'):
            self.period=self.forward_period if self.mode=='step' and command['vx_m_s']>0 else self.step_period
            self.end=t+self.period
            lower,upper=-np.inf,np.inf
            for leg,interval in ((self.stance,self.period),(self.swing,self.shift_fraction*self.period)):
                relative=self.foot_headings[leg]-self.heading
                lower=max(lower,(relative-.072)/interval)
                upper=min(upper,(relative+.072)/interval)
            self.yaw_rate=float(np.clip(self.yaw_rate,lower,upper))
            self.target_x=self.feet[self.stance,0]+(command['vx_m_s'] if self.mode=='step' else 0.)*self.period
            inset=.024+self.steady_inset_delta*np.clip((self.motion_steps-1)/2,0.,1.)
            self.target_y=self.feet[self.stance,1]-(1 if self.stance==0 else -1)*inset
            self.target_offset=0.
            self.swing_heading_target=self.heading+(1.45+.5*self.shift_fraction)*self.period*self.yaw_rate

    def heading_geometry(self,t):
        elapsed=np.clip(t-self.start,0.,self.end-self.start)
        heading=self.from_heading+self.yaw_rate*elapsed
        feet=self.from_foot_headings.copy()
        if self.mode in ('step','align'):
            u=np.clip((elapsed-self.shift_fraction*self.period)/((.9-self.shift_fraction)*self.period),0.,1.)
            blend=u*u*(3-2*u)
            feet[self.swing]+=(self.swing_heading_target-feet[self.swing])*blend
        return heading,feet

    def geometry(self,t):
        feet,xy,support,offset=super().geometry(t)
        if self.mode in ('step','align'):
            u=np.clip(t-self.start,0.,self.period)
            shift=self.smooth(u/(self.shift_fraction*self.period))
            xy[1]=self.from_xy[1]+(self.target_y-self.from_xy[1])*shift
            support=(1-shift)*self.from_support+shift*np.eye(2)[self.stance]
            fraction=np.clip((u-self.shift_fraction*self.period)/((.9-self.shift_fraction)*self.period),0.,1.)
            feet[self.swing,0]=self.feet[self.swing,0]+(self.target_x-self.feet[self.swing,0])*self.smooth(fraction)
            if self.swing_profile=="quartic":
                feet[self.swing,2]=.004*16*fraction**2*(1-fraction)**2
            else:
                feet[self.swing,2]=.004*(64*fraction**3*(1-fraction)**3)
        return feet,xy,support,offset

    def sample(self,t):
        sample=super().sample(t)
        heading,feet_heading=self.heading_geometry(t)
        q=[]
        for leg,side in enumerate(('left','right')):
            sole=self.kinematics.legacy.fk_leg(sample.q[leg*5:leg*5+5],side,sample.base)[1]
            relative=feet_heading[leg]-heading
            solved,_,_=self.kinematics.solve_flat_foot(sole[:3,3],relative,side,sample.base)
            q.extend(solved)
        return SimpleNamespace(**vars(sample),q12=np.array(q),virtual_heading=heading)
