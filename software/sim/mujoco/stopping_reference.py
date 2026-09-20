"""Experimental final-foot alignment and slower return to double support."""
from types import SimpleNamespace
import numpy as np
from probe_reference_gait import MovingCOMReference


class AlignedStopReference(MovingCOMReference):
    def __init__(self,*args,finish_shift_s=.3,**kwargs):
        super().__init__(*args,**kwargs)
        if not np.isfinite(finish_shift_s) or not 0 < finish_shift_s <= .4:
            raise ValueError('finish shift must be in (0,.4] seconds to fit the probe finish window')
        self.finish_shift_s = finish_shift_s

    def sample(self,time_s):
        g = self.g
        period = g['shift_s']+g['swing_s']+g['settle_s']
        t = time_s-g['initial_stand_s']
        last_start = (self.steps-1)*period
        if t < last_start:
            return super().sample(time_s)
        feet = self.initial_feet.copy()
        previous_y = feet[:,1].mean()
        previous_support = np.array([.5,.5])
        for n in range(self.steps-1):
            stance,swing = n%2,1-n%2
            feet[swing,0] = feet[stance,0]+g['step_length_m']
            previous_y = feet[stance,1]-(1 if stance==0 else -1)*g['com_inset_mm']/1000
            previous_support = np.eye(2)[stance]
        stance,swing = (self.steps-1)%2,1-(self.steps-1)%2
        u = t-last_start
        target_x = feet[stance,0]
        stance_y = feet[stance,1]-(1 if stance==0 else -1)*g['com_inset_mm']/1000
        if u < period:
            blend = self.smooth(u/g['shift_s'])
            from_x = feet[:,0].mean()
            xy = np.array([from_x+(target_x-from_x)*self.smooth(u/period),
                           previous_y+(stance_y-previous_y)*blend])
            support = (1-blend)*previous_support+blend*np.eye(2)[stance]
            phase = 'stop_weight_shift'
            if u >= g['shift_s']:
                fraction = np.clip((u-g['shift_s'])/g['swing_s'],0,1)
                feet[swing,0] += (target_x-feet[swing,0])*self.smooth(fraction)
                feet[swing,2] = g['step_height_m']*16*fraction**2*(1-fraction)**2
                phase = 'stop_align_'+self.sides[swing]
        else:
            feet[:,0] = target_x
            blend = self.smooth((u-period)/self.finish_shift_s)
            xy = feet.mean(axis=0)[:2]
            xy[1] = stance_y+(xy[1]-stance_y)*blend
            support = (1-blend)*np.eye(2)[stance]+blend*np.array([.5,.5])
            phase = 'stop_double_support'
        xy[0] += self.com_forward_offset_m
        q,base,error = self.pose(feet,xy,self.seed,self.b0[2,3])
        self.seed = (q,base)
        return SimpleNamespace(q=q,base=base,support=support,phase=phase)
