"""Pure-NumPy servo model, updated at EACH MuJoCo physics step.

The source MJCF contains torque motors. Position targets must NEVER be written
straight into data.ctrl. No feed-forward root forces or gravity cancellation.
This is a datasheet-envelope approximation, not a system-identified servo model.
"""
from __future__ import annotations
from collections import deque
import numpy as np


def bounded_target(action: np.ndarray, home: np.ndarray, limits: np.ndarray, cfg: dict) -> np.ndarray:
    a = np.asarray(action, dtype=np.float64)
    if a.shape != (10,) or not np.isfinite(a).all():
        raise ValueError("Action must be ten finite values")
    target = home + np.asarray(cfg["action_scale_rad"]) * np.clip(a, -1.0, 1.0)
    margin = cfg["target_joint_margin_rad"]
    target = np.clip(target, limits[:, 0] + margin, limits[:, 1] - margin)
    # R5 has a coupled outward-splay interference. This is a conservative SEARCH
    # guard, not a claim that the entire remaining joint space is CAD-validated.
    spread = target[0] - target[5]
    excess = max(0.0, spread - cfg["max_outward_hip_spread_rad"])
    target[0] -= excess / 2
    target[5] += excess / 2
    return target


class ServoBank:
    def __init__(self, motor: dict[str, np.ndarray], physics_dt: float, slew: float):
        self.dt = float(physics_dt)
        if self.dt <= 0 or slew <= 0:
            raise ValueError("dt and slew must be positive")
        self.slew = float(slew)
        for key in ("cap", "stall", "omega", "kp", "kd"):
            setattr(self, key, np.asarray(motor[key], dtype=float).copy())
        delay = np.asarray(motor["delay_s"], dtype=float)
        if not np.allclose(delay, delay[0]) or delay[0] < 0:
            raise ValueError("This bank expects one nonnegative shared command delay")
        self.delay_ticks = int(round(float(delay[0]) / self.dt))
        self.strength = 1.0
        self.reset(np.zeros(10))

    def reset(self, target: np.ndarray, strength: float = 1.0) -> None:
        if not 0 < strength <= 1.0:
            raise ValueError("Motor strength scale must be in (0,1]")
        self.strength = float(strength)
        self.filtered = np.asarray(target, dtype=float).copy()
        self.delayed = self.filtered.copy()
        self.queue = deque((self.filtered.copy() for _ in range(self.delay_ticks + 1)),
                           maxlen=self.delay_ticks + 1)

    def step(self, q: np.ndarray, qd: np.ndarray, target: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        # Slew limiting prevents an ideal servo from following discontinuous targets.
        self.filtered += np.clip(target - self.filtered, -self.slew * self.dt, self.slew * self.dt)
        self.queue.append(self.filtered.copy())
        self.delayed = self.queue[0]
        raw = self.kp * (self.delayed - q) - self.kd * qd
        motoring = raw * qd > 0.0
        available = np.where(motoring, self.stall * np.maximum(0.0, 1.0 - np.abs(qd) / self.omega), self.stall)
        bound = np.minimum(self.cap, available) * self.strength
        tau = np.clip(raw, -bound, bound)
        return tau, np.abs(raw) > bound + 1e-10, bound


class PostSlewLowPassBank(ServoBank):
    """Same implementation as the user's tested 40 ms control probe.

    Independent slew and LP states; the original bank then retains its final
    rate guard, transport delay, PD, torque/speed envelope and derating. The
    final guard is redundant for valid equal initial states, retained to match
    the diagnostic exactly. `filtered` is POST-LP, PRE-transport-delay.
    """
    def __init__(self, motor, physics_dt: float, slew: float, time_constant_s: float):
        import math
        if not math.isfinite(time_constant_s) or time_constant_s < 0:
            raise ValueError("time_constant_s must be finite and nonnegative")
        self.time_constant_s = float(time_constant_s)
        self.alpha = (-math.expm1(-float(physics_dt) / self.time_constant_s)
                      if self.time_constant_s else 1.0)
        super().__init__(motor, physics_dt, slew)

    def reset(self, target, strength: float = 1.0):
        super().reset(target, strength)
        self.slew_stage = self.filtered.copy()
        self.lowpass_stage = self.filtered.copy()

    def step(self, q, qd, target):
        if self.time_constant_s == 0.0:
            return super().step(q, qd, target)
        self.slew_stage += np.clip(np.asarray(target) - self.slew_stage,
                                   -self.slew*self.dt, self.slew*self.dt)
        self.lowpass_stage += self.alpha * (self.slew_stage-self.lowpass_stage)
        return super().step(q, qd, self.lowpass_stage)


def make_servo_bank(motor, physics_dt: float, env_config: dict) -> ServoBank:
    tau = env_config.get("target_lowpass_time_constant_s", 0.0)
    if tau == 0.0:
        # Exact original path, not a near-identity numerical filter.
        return ServoBank(motor, physics_dt, env_config["target_slew_rad_s"])
    return PostSlewLowPassBank(motor, physics_dt, env_config["target_slew_rad_s"], tau)
