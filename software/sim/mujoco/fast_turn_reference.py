"""Development-only r9 stepping with a 0.24 rad heading guard.

Derived from the frozen r8 reference; r8 source remains unchanged.

The virtual heading is used only for leg IK. It never sets the simulated root.
Commands are latched at step boundaries so a foot is not reset while planted.
"""
from types import SimpleNamespace
import numpy as np
from maneuver_reference import CommandReference


class FastTurnReference(CommandReference):
    initial_inset_mm = 24.
    heading_goal_rad = None

    def __init__(self, initial, pose, smooth, protocol, kinematics, shift_fraction=.35, steady_inset_mm=25.5, step_period=.32, forward_period=None, swing_profile="quartic", forward_stance_width_mm=None, backward_settle_fraction=.1, backward_shift_fraction=None):
        if not np.isfinite(shift_fraction) or not .2<=shift_fraction<=.5:raise ValueError('shift fraction outside [.2,.5]')
        if not np.isfinite(steady_inset_mm) or not 20<=steady_inset_mm<26:raise ValueError('steady inset outside [20,26) mm')
        if not np.isfinite(step_period) or not .24<=step_period<=.4:raise ValueError('step period outside [.24,.4] seconds')
        if swing_profile not in ("quartic","c2"):raise ValueError("unknown swing profile")
        if forward_stance_width_mm is not None and (not np.isfinite(forward_stance_width_mm) or not 58<=forward_stance_width_mm<=70):
            raise ValueError('forward stance width outside [58,70] mm')
        if not np.isfinite(backward_settle_fraction) or not .1<=backward_settle_fraction<=.3:
            raise ValueError("backward settle fraction outside [.1,.3]")
        if backward_shift_fraction is not None and (not np.isfinite(backward_shift_fraction) or not .2<=backward_shift_fraction<=.5):
            raise ValueError("backward shift fraction outside [.2,.5]")
        self.backward_shift_fraction=backward_shift_fraction
        self.nominal_shift_fraction=shift_fraction
        self.backward_settle_fraction=backward_settle_fraction
        self.forward_stance_width_mm=forward_stance_width_mm
        self.neutral_foot_y=initial.initial_feet[:,1].copy()
        self.swing_profile=swing_profile
        self.shift_fraction=shift_fraction
        self.steady_inset_delta=(steady_inset_mm-self.initial_inset_mm)/1000
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
        goal_reached = self.heading_goal_rad is not None and abs(self.heading-self.heading_goal_rad)<1e-8
        if goal_reached:
            self.protocol['segments'][0].update(vx_m_s=0.,yaw_rate_rad_s=0.)
        super().begin(t)
        index=min(np.searchsorted(self.boundaries,t+1e-9,side='right')-1,len(self.protocol['segments'])-1)
        command=self.protocol['segments'][index]
        self.shift_fraction=self.backward_shift_fraction if command['vx_m_s']<0 and self.backward_shift_fraction is not None else self.nominal_shift_fraction
        self.swing_end_fraction=1-self.backward_settle_fraction if command['vx_m_s']<0 else .9
        self.desired_foot_y=self.neutral_foot_y.copy()
        if self.forward_stance_width_mm is not None and command['vx_m_s']>0 and self.motion_steps>=2:
            self.desired_foot_y=self.neutral_foot_y.mean()+np.array([1.,-1.])*self.forward_stance_width_mm/2000
        width_alignment=self.forward_stance_width_mm is not None and np.max(abs(self.feet[:,1]-self.desired_foot_y))>1e-9
        if not goal_reached and command['vx_m_s']==0 and command['yaw_rate_rad_s']==0 and (np.max(abs(self.foot_headings-self.heading))>1e-9 or width_alignment):
            self.mode='align'
            self.swing=1-self.stance
        self.yaw_rate=command['yaw_rate_rad_s'] if self.mode=='step' else 0.
        self.from_heading=self.heading
        self.from_foot_headings=self.foot_headings.copy()
        if self.mode in ('step','align'):
            self.period=self.forward_period if self.mode=='step' and command['vx_m_s']>0 else self.step_period
            self.end=t+self.period
            # Hold heading while shifting load. Rotate only during the swing,
            # reserving yaw travel for the planted foot throughout the step.
            relative=self.foot_headings[self.stance]-self.heading
            delta=np.clip(self.yaw_rate*self.period,relative-.22,relative+.22)
            final_step=False
            if self.heading_goal_rad is not None:
                remaining=self.heading_goal_rad-self.heading
                if delta*remaining>=0 and abs(delta)>=abs(remaining):
                    delta=remaining
                    final_step=True
            self.yaw_rate=float(delta/self.period)
            self.target_x=self.feet[self.stance,0]+(command['vx_m_s'] if self.mode=='step' else 0.)*self.period
            inset=self.initial_inset_mm/1000+self.steady_inset_delta*np.clip((self.motion_steps-1)/2,0.,1.)
            self.target_y=self.feet[self.stance,1]-(1 if self.stance==0 else -1)*inset
            self.target_offset=0.
            self.swing_heading_target=self.heading+self.period*self.yaw_rate+np.sign(self.yaw_rate)*.10
            if final_step:self.swing_heading_target=self.heading_goal_rad

    def heading_geometry(self,t):
        elapsed=np.clip(t-self.start,0.,self.end-self.start)
        heading=self.from_heading
        feet=self.from_foot_headings.copy()
        if self.mode in ('step','align'):
            u=np.clip((elapsed-self.shift_fraction*self.period)/((self.swing_end_fraction-self.shift_fraction)*self.period),0.,1.)
            blend=u*u*(3-2*u)
            heading+=self.yaw_rate*self.period*blend
            feet[self.swing]+=(self.swing_heading_target-feet[self.swing])*blend
        return heading,feet

    def geometry(self,t):
        feet,xy,support,offset=super().geometry(t)
        if self.mode in ('step','align'):
            u=np.clip(t-self.start,0.,self.period)
            shift=self.smooth(u/(self.shift_fraction*self.period))
            xy[1]=self.from_xy[1]+(self.target_y-self.from_xy[1])*shift
            support=(1-shift)*self.from_support+shift*np.eye(2)[self.stance]
            fraction=np.clip((u-self.shift_fraction*self.period)/((self.swing_end_fraction-self.shift_fraction)*self.period),0.,1.)
            feet[self.swing,0]=self.feet[self.swing,0]+(self.target_x-self.feet[self.swing,0])*self.smooth(fraction)
            if self.forward_stance_width_mm is not None:
                feet[self.swing,1]=self.feet[self.swing,1]+(self.desired_foot_y[self.swing]-self.feet[self.swing,1])*self.smooth(fraction)
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
