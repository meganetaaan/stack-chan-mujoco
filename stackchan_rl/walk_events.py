"""Conservative contact events and forward progress for the v2 walk objective.

No MuJoCo dependency: inputs are measured sole contacts/heights/positions. Raw
contact observations keep their v1 meaning. Confirmation is for event counting,
not a fabricated force or a change to the collision model.
"""
from __future__ import annotations
import numpy as np


class WalkEventTracker:
    def __init__(self, dt: float, env_config: dict):
        self.dt = float(dt)
        self.min_air = env_config["minimum_airtime_s"]
        self.min_lift = env_config["minimum_lift_m"]
        self.confirm_s = env_config["landing_contact_confirm_s"]
        self.min_advance = env_config["minimum_foot_advance_m"]
        self.cooldown = env_config["event_cooldown_s"]
        self.t = self.active_time = 0.0
        self._active = False
        self._base_highwater = None
        self._last_step_at = 0.0
        self.last_reward_lift = self.last_reward_landing = None
        self.last_lift_at = self.last_landing_at = -1e9
        self.airtime = np.zeros(2)
        self.supported_airtime = np.zeros(2)
        self.peak = np.zeros(2)
        self.peak_episode = np.zeros(2)
        self.ground_time = np.zeros(2)
        self.touched = np.zeros(2, dtype=bool)
        self.in_air = np.zeros(2, dtype=bool)
        self.lift_credited = np.zeros(2, dtype=bool)
        self.origin = np.zeros((2, 2))
        self.last_ground = np.zeros((2, 2))
        self.foot_highwater = np.full(2, -np.inf)
        self.pending = [None, None]
        self.counts = np.zeros(2, dtype=int)
        self.liftoffs = np.zeros(2, dtype=int)
        self.forward_counts = np.zeros(2, dtype=int)
        self.raw_unloads = np.zeros(2, dtype=int)
        self.sequence: list[str] = []
        self.forward_sequence: list[str] = []
        self.previous_contacts = np.zeros(2, dtype=bool)
        self.rejected = {"short_airtime": 0, "low_clearance": 0,
                         "insufficient_other_support": 0, "unconfirmed_touch": 0}
        self.last_events: dict = {}

    def _qualified(self, i: int) -> bool:
        return bool(self.touched[i] and self.airtime[i] + 1e-10 >= self.min_air
                    and self.peak[i] + 1e-10 >= self.min_lift
                    and self.supported_airtime[i] + 1e-10 >= 0.5 * self.airtime[i])

    def update(self, contacts, heights, feet_xy, base_forward: float, active: bool) -> dict:
        contacts = np.asarray(contacts, dtype=bool)
        heights = np.asarray(heights, dtype=float)
        xy = np.asarray(feet_xy, dtype=float)
        if contacts.shape != (2,) or heights.shape != (2,) or xy.shape != (2, 2):
            raise ValueError("Expected two sole contacts, two heights and 2x2 episode-frame positions")
        if not np.isfinite(heights).all() or not np.isfinite(xy).all() or not np.isfinite(base_forward):
            raise ValueError("Nonfinite foot/body event input")
        self.t += self.dt
        out = {"valid_landings_this_step": 0, "qualified_liftoffs_this_step": 0,
               "rewarded_liftoffs_this_step": 0, "rewarded_landings_this_step": 0,
               "forward_landings_this_step": 0, "alternating_landings_this_step": 0,
               "new_forward_distance_m": 0.0, "no_step_elapsed_s": 0.0,
               "valid_landing_feet": [], "forward_landing_feet": []}
        if active:
            if not self._active:
                self._base_highwater = float(base_forward)
                self.active_time = self._last_step_at = 0.0
            self.active_time += self.dt
            out["new_forward_distance_m"] = max(0.0, float(base_forward) - self._base_highwater)
            self._base_highwater = max(self._base_highwater, float(base_forward))
        else:
            self.active_time = self._last_step_at = 0.0
            self._base_highwater = float(base_forward)
        self._active = active

        for i in range(2):
            if not contacts[i]:
                if not self.in_air[i]:
                    if self.pending[i] is not None:
                        self.rejected["unconfirmed_touch"] += 1
                    self.pending[i] = None
                    self.in_air[i] = True
                    self.airtime[i] = self.supported_airtime[i] = self.peak[i] = 0.0
                    self.lift_credited[i] = False
                    self.origin[i] = self.last_ground[i]
                    if self.previous_contacts[i] and self.touched[i]:
                        self.raw_unloads[i] += 1
                self.ground_time[i] = 0.0
                if self.touched[i]:
                    self.airtime[i] += self.dt
                    self.supported_airtime[i] += self.dt * float(contacts[1-i])
                    self.peak[i] = max(self.peak[i], float(heights[i]))
                    self.peak_episode[i] = max(self.peak_episode[i], self.peak[i])
                    if self._qualified(i) and not self.lift_credited[i]:
                        self.lift_credited[i] = True
                        self.liftoffs[i] += 1
                        out["qualified_liftoffs_this_step"] += 1
                        # No repeated same-leg or rapid-tapping liftoff bonuses.
                        if (active and self.last_reward_lift != i
                            and self.t-self.last_lift_at+1e-10 >= self.cooldown):
                            out["rewarded_liftoffs_this_step"] += 1
                            self.last_reward_lift, self.last_lift_at = i, self.t
            else:
                if self.in_air[i]:
                    good = self._qualified(i)
                    if self.touched[i] and not good:
                        if self.airtime[i]+1e-10 < self.min_air:
                            self.rejected["short_airtime"] += 1
                        elif self.peak[i]+1e-10 < self.min_lift:
                            self.rejected["low_clearance"] += 1
                        else:
                            self.rejected["insufficient_other_support"] += 1
                    self.pending[i] = {"valid": good, "origin": self.origin[i].copy()}
                    self.in_air[i] = False
                    self.ground_time[i] = 0.0
                self.ground_time[i] += self.dt
                if self.ground_time[i]+1e-10 >= self.confirm_s:
                    pending = self.pending[i]
                    if pending is not None and pending["valid"]:
                        self.counts[i] += 1
                        self.sequence.append("left" if i == 0 else "right")
                        out["valid_landings_this_step"] += 1
                        out["valid_landing_feet"].append(i)
                        if active:
                            self._last_step_at = self.active_time
                        if (active and self.last_reward_landing != i
                            and self.t-self.last_landing_at+1e-10 >= self.cooldown):
                            out["rewarded_landings_this_step"] += 1
                            if self.last_reward_landing is not None:
                                out["alternating_landings_this_step"] += 1
                            self.last_reward_landing, self.last_landing_at = i, self.t
                        # Both swing advance and a new per-foot forward record
                        # are required. Lifting in place/sliding never qualifies.
                        advanced = (xy[i,0]-pending["origin"][0]+1e-10 >= self.min_advance
                                    and xy[i,0]-self.foot_highwater[i]+1e-10 >= self.min_advance)
                        if advanced:
                            self.forward_counts[i] += 1
                            self.forward_sequence.append("left" if i == 0 else "right")
                            out["forward_landings_this_step"] += 1
                            out["forward_landing_feet"].append(i)
                    self.pending[i] = None
                    self.touched[i] = True
                    self.last_ground[i] = xy[i]
                    self.foot_highwater[i] = max(self.foot_highwater[i], float(xy[i,0]))
                    self.airtime[i] = self.supported_airtime[i] = self.peak[i] = 0.0
        self.previous_contacts[:] = contacts
        if active:
            out["no_step_elapsed_s"] = self.active_time-self._last_step_at
        self.last_events = out
        return out

    def summary(self) -> dict:
        return {"qualified_liftoffs": self.liftoffs.tolist(),
                "forward_landings": self.forward_counts.tolist(),
                "forward_landing_sequence": list(self.forward_sequence),
                "raw_unloads": self.raw_unloads.tolist(),
                "max_sole_clearance_m": self.peak_episode.tolist(),
                "event_rejections": dict(self.rejected),
                "seconds_without_valid_landing": float(self.last_events.get("no_step_elapsed_s", 0.0))}
