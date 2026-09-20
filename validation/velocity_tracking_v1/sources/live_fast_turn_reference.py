"""Interactive adapter for the frozen r9 fast-turn reference.

Only references change; root motion comes entirely from actuator-driven physics.
"""
import numpy as np
from fast_turn_reference import FastTurnReference


class LiveFastTurnReference(FastTurnReference):
    initial_inset_mm = 25.5
    commands = {'stop': (0., 0.), 'forward': (.04, 0.),
                'backward': (-.02, 0.), 'left': (0., np.deg2rad(40.)),
                'right': (0., -np.deg2rad(40.))}

    def __init__(self, initial, pose, smooth, protocol, kinematics):
        super().__init__(initial, pose, smooth, protocol, kinematics,
                         .45, 25.5, .4, .4, 'quartic', None, .1, .45)

    def set_command(self, name, t):
        vx, wz = self.commands[name] if isinstance(name,str) else name
        if not isinstance(name,str):
            previous=self.protocol['segments'][0]
            if not vx and not wz and self.mode=='step' and previous['yaw_rate_rad_s'] and not previous['vx_m_s']:
                # Finish the current pivot and settle with its existing foot
                # headings, avoiding two unnecessary zero-speed alignment steps.
                self.heading_goal_rad=self.heading_geometry(self.end)[0]
            elif vx or wz:
                self.heading_goal_rad=None
        self.protocol['segments'][0].update(vx_m_s=vx, yaw_rate_rad_s=wz)
        if self.mode == 'stand' and (vx or wz):
            if wz:self.stance = 0 if wz > 0 else 1
            self.end = t


    def begin(self,t):
        super().begin(t)
        command=self.protocol['segments'][0]
        if self.mode=='step' and command['vx_m_s'] and self.yaw_rate:
            # Differential travel of inner/outer feet about the body heading.
            # Translation-only and pivot references remain unchanged.
            delta=self.yaw_rate*self.period
            self.target_x-=.5*(self.feet[self.swing,1]-self.feet[self.stance,1])*np.sin(delta)
