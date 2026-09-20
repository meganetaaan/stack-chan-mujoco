"""Continuous ten-axis joint references for commanded stepping and stopping.

Yaw is NOT imposed on the root or feet. A separate controller must create real
yaw through the floating plant. These references alone cannot satisfy turns.
"""
from types import SimpleNamespace
import numpy as np
from stackchan_rl.maneuver_protocol import validate


class CommandReference:
    def __init__(self, initial, pose, smooth, protocol):
        self.pose, self.smooth = pose, smooth
        self.protocol = protocol
        self.boundaries = validate(protocol)
        self.feet = initial.initial_feet.copy()
        self.seed = (initial.q0.copy(), initial.b0.copy())
        self.height = initial.b0[2, 3]
        self.xy = self.feet.mean(axis=0)[:2]
        self.support = np.array([.5, .5])
        self.offset = 0.
        self.stance = 0
        self.last_t = -1.
        self.begin(0.)

    def begin(self, t):
        index = min(np.searchsorted(self.boundaries, t+1e-9, side='right')-1,
                    len(self.protocol['segments'])-1)
        command = self.protocol['segments'][index]
        moving = command['vx_m_s'] != 0 or command['yaw_rate_rad_s'] != 0
        self.start = t
        self.from_xy, self.from_support = self.xy.copy(), self.support.copy()
        self.from_offset = self.offset
        if moving or abs(self.feet[0, 0]-self.feet[1, 0]) > 1e-9:
            self.mode = 'step' if moving else 'align'
            vx = command['vx_m_s'] if moving else 0.
            self.period = .27 if vx > 0 else .32
            self.end = t+self.period
            self.swing = 1-self.stance
            self.target_x = self.feet[self.stance, 0]+vx*self.period
            self.target_y = self.feet[self.stance, 1]-(1 if self.stance == 0 else -1)*.024
            self.target_offset = -.0015 if vx < 0 else 0.
        elif not np.allclose(self.support, [.5, .5], atol=1e-12) or abs(self.offset)>1e-12:
            self.mode = 'settle'
            self.period = .3
            self.end = t+self.period
        else:
            self.mode = 'stand'
            self.end = self.boundaries[index+1]
            if self.end <= t+1e-9:
                self.end = np.inf

    def geometry(self, t):
        feet = self.feet.copy()
        xy, support, offset = self.from_xy.copy(), self.from_support.copy(), self.from_offset
        if self.mode in ('step', 'align'):
            u = np.clip(t-self.start, 0., self.period)
            shift = self.smooth(u/(.35*self.period))
            progress = self.smooth(u/self.period)
            offset += (self.target_offset-self.from_offset)*progress
            target_mean_x = (feet[self.stance, 0]+self.target_x)/2
            xy = np.array([feet[:, 0].mean()+(target_mean_x-feet[:, 0].mean())*progress+offset,
                           self.from_xy[1]+(self.target_y-self.from_xy[1])*shift])
            support = (1-shift)*self.from_support+shift*np.eye(2)[self.stance]
            fraction = np.clip((u-.35*self.period)/(.55*self.period), 0., 1.)
            feet[self.swing, 0] += (self.target_x-feet[self.swing, 0])*self.smooth(fraction)
            feet[self.swing, 2] = .004*16*fraction**2*(1-fraction)**2
        elif self.mode == 'settle':
            blend = self.smooth((t-self.start)/self.period)
            xy += (feet.mean(axis=0)[:2]-self.from_xy)*blend
            support += (np.array([.5, .5])-self.from_support)*blend
            offset *= 1-blend
        return feet, xy, support, offset

    def sample(self, t):
        if not np.isfinite(t) or t < self.last_t or t < 0 or t > self.boundaries[-1]+1e-8:
            raise ValueError('sample chronologically within the command schedule')
        while t >= self.end-1e-10:
            self.feet, self.xy, self.support, self.offset = self.geometry(self.end)
            if self.mode in ('step', 'align'):
                self.stance = 1-self.stance
            self.begin(self.end)
        feet, xy, support, _ = self.geometry(t)
        q, base, _ = self.pose(feet, xy, self.seed, self.height)
        self.seed = (q, base)
        self.last_t = t
        return SimpleNamespace(q=q, base=base, support=support, phase=self.mode)
