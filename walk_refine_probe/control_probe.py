"""Diagnostic-only, optional post-slew low-pass. No actuator-strength change.

The original v3 ServoBank is authoritative for delay, PD and torque/speed limits.
A zero time constant calls its original step directly (regression tested).
This module does NOT modify the installed stackchan_rl sources or checkpoints.
"""
from __future__ import annotations
import math
import numpy as np
from stackchan_rl.actuation import ServoBank

class PostSlewLowPassBank(ServoBank):
    def __init__(self, motor, physics_dt: float, slew: float, time_constant_s: float):
        if not math.isfinite(time_constant_s) or time_constant_s < 0:
            raise ValueError('time_constant_s must be finite and nonnegative')
        self.time_constant_s = float(time_constant_s)
        self.alpha = (-math.expm1(-float(physics_dt)/self.time_constant_s)
                      if self.time_constant_s else 1.0)
        super().__init__(motor, physics_dt, slew)

    def reset(self, target, strength: float = 1.0):
        super().reset(target, strength)
        self.slew_stage = self.filtered.copy()
        self.lowpass_stage = self.filtered.copy()

    def step(self, q, qd, target):
        if self.time_constant_s == 0.0:
            return super().step(q, qd, target)
        self.slew_stage += np.clip(np.asarray(target)-self.slew_stage,
                                   -self.slew*self.dt, self.slew*self.dt)
        self.lowpass_stage += self.alpha*(self.slew_stage-self.lowpass_stage)
        # Original bank retains the bound as a final guard and performs all
        # delay/PD/torque limiting. Low-pass following the bounded-rate signal
        # cannot exceed that rate when reset to the same initial target.
        return super().step(q, qd, self.lowpass_stage)
