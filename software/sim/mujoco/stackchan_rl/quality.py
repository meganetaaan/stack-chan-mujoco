"""v3 gait-quality measurements; NumPy only, no simulated or fabricated forces.

Input samples come from MuJoCo's solved physics stages (nominally 1 kHz), not
from the renderer. The 50 Hz v2 foot-event tracker remains authoritative for
qualified *steps*. A raw touchdown here is a diagnostic, NOT a rewarded step.
Body axes follow the model: +X forward, +Y left, +Z up. gyro[1] is pitch rate.
"""
from __future__ import annotations
from collections import deque
import math
import numpy as np


def body_angles(R: np.ndarray) -> tuple[float, float]:
    """ZYX roll, pitch, in radians. No Euler differentiation is used for rates."""
    R = np.asarray(R, dtype=float)
    return float(np.arctan2(R[2, 1], R[2, 2])), float(np.arcsin(np.clip(-R[2, 0], -1., 1.)))


class GaitQuality:
    """Accumulate read-only substep telemetry and bounded, moving-window events.

    Initial drop is excluded from episode-quality metrics by measurement_start_s.
    Rate costs are interval MEANS (caller integrates dt); touchdown costs are
    interval SUMS (caller must not multiply by dt). No arbitrary equal-load
    requirement is imposed on left/right stance, nor equality on joint angles.
    """
    def __init__(self, env: dict, weights: dict, body_weight_N: float):
        if not math.isfinite(body_weight_N) or body_weight_N <= 0:
            raise ValueError('body_weight_N must be positive')
        self.env, self.w, self.bw = env, weights, float(body_weight_N)
        self.start_s = env['measurement_start_s']
        self.confirm_air = env['touchdown_min_airtime_s']
        self.air = np.zeros(2)
        self.seen_support = np.zeros(2, dtype=bool)
        self.was_contact = np.zeros(2, dtype=bool)
        self.recent_forward = deque()
        self.last_landing = None
        self.last_landing_time = -np.inf
        self.n = self.action_n = 0
        self.gyro_sq = np.zeros(3)
        self.gyro_peak = np.zeros(3)
        self.pitch_sum = self.pitch_sq = 0.
        self.pitch_min, self.pitch_max = np.inf, -np.inf
        self.roll_sq = 0.
        self.load_peak = np.zeros(2)
        self.load_excess_sum = 0.
        self.touchdowns = np.zeros(2, dtype=int)
        self.td_speed_sq = np.zeros(2)
        self.td_speed_peak = np.zeros(2)
        self.action_delta_sq = self.action_delta2_sq = 0.
        self.target_error_sq = np.zeros(10)
        self.window_balance_integral = self.window_balance_time = 0.
        self.repeat_count = 0
        self.begin_interval()

    def begin_interval(self) -> None:
        self.i_n = 0
        self.i_gyro_sq = np.zeros(3)
        self.i_pitch_excess = self.i_load_excess = self.i_touchdown_cost = 0.
        self.i_load_peak = np.zeros(2)
        self.i_td_speed_peak = np.zeros(2)
        self.i_touchdowns = np.zeros(2, dtype=int)

    def observe(self, *, time_s: float, dt: float, gyro, roll: float, pitch: float,
                loads, contact_down_speed) -> None:
        """One solved physics sample. contact_down_speed uses v + omega x r.

        Loads are sums of the vertical sole-ground reaction forces per foot.
        A touchdown needs a prior supported state and >=40 ms without support;
        initial free fall and short contact chatter cannot generate events.
        """
        gyro = np.asarray(gyro, dtype=float)
        loads = np.maximum(0., np.asarray(loads, dtype=float))
        speed = np.maximum(0., np.asarray(contact_down_speed, dtype=float))
        if gyro.shape != (3,) or loads.shape != (2,) or speed.shape != (2,):
            raise ValueError('Invalid substep telemetry shapes')
        if not np.isfinite(np.r_[gyro, loads, speed, roll, pitch, time_s, dt]).all() or dt <= 0:
            raise ValueError('Nonfinite substep telemetry or nonpositive dt')
        contacts = loads > self.env['contact_threshold_N']
        touchdown = contacts & ~self.was_contact & self.seen_support & (self.air + 1e-10 >= self.confirm_air)
        self.air = np.where(contacts, 0., self.air + dt)
        self.seen_support |= contacts
        self.was_contact = contacts
        if time_s + 1e-10 < self.start_s:
            return
        pitch_free = np.deg2rad(self.w['pitch_free_deg'])
        pitch_scale = np.deg2rad(self.w['pitch_scale_deg'])
        pitch_cost = min(16., (max(0., abs(pitch)-pitch_free)/pitch_scale)**2)
        load_cost = float(np.minimum(25., np.maximum(0., loads/self.bw-self.w['impact_free_bw'])**2).sum())
        td = np.minimum(9., (np.maximum(0., speed-self.w['touchdown_free_speed_m_s'])/self.w['touchdown_speed_scale_m_s'])**2)
        self.i_n += 1
        self.i_gyro_sq += gyro**2
        self.i_pitch_excess += pitch_cost
        self.i_load_excess += load_cost
        self.i_touchdown_cost += float(np.sum(td*touchdown))
        self.i_load_peak = np.maximum(self.i_load_peak, loads)
        self.i_td_speed_peak = np.maximum(self.i_td_speed_peak, speed*touchdown)
        self.i_touchdowns += touchdown.astype(int)
        self.n += 1
        self.gyro_sq += gyro**2
        self.gyro_peak = np.maximum(self.gyro_peak, np.abs(gyro))
        self.pitch_sum += pitch
        self.pitch_sq += pitch**2
        self.pitch_min, self.pitch_max = min(self.pitch_min, pitch), max(self.pitch_max, pitch)
        self.roll_sq += roll**2
        self.load_peak = np.maximum(self.load_peak, loads)
        self.load_excess_sum += load_cost
        self.touchdowns += touchdown.astype(int)
        self.td_speed_sq += speed**2*touchdown
        self.td_speed_peak = np.maximum(self.td_speed_peak, speed*touchdown)

    def finish_interval(self, *, time_s: float, dt: float, moving: bool, events: dict,
                        action_delta, action_delta2, target_error) -> dict:
        measured = time_s + 1e-10 >= self.start_s
        if measured:
            arrays = [np.asarray(a, dtype=float) for a in (action_delta, action_delta2, target_error)]
            if any(a.shape != (10,) or not np.isfinite(a).all() for a in arrays):
                raise ValueError('Expected ten finite action/target-error values')
            self.action_n += 1
            self.action_delta_sq += float(np.mean(arrays[0]**2))
            self.action_delta2_sq += float(np.mean(arrays[1]**2))
            self.target_error_sq += arrays[2]**2
        repeat = 0
        if moving:
            for i in events.get('valid_landing_feet', []):
                if self.last_landing == i and time_s-self.last_landing_time <= self.env['quality_window_s']:
                    repeat += 1
                self.last_landing, self.last_landing_time = i, time_s
            for i in events.get('forward_landing_feet', []):
                self.recent_forward.append((time_s, int(i)))
        else:
            self.recent_forward.clear()
            self.last_landing, self.last_landing_time = None, -np.inf
        while self.recent_forward and self.recent_forward[0][0] < time_s-self.env['quality_window_s']:
            self.recent_forward.popleft()
        counts = np.bincount([i for _, i in self.recent_forward], minlength=2)
        # One extra step is normal in alternating walking. Only additional
        # imbalance is charged; the window lets recovery erase an old mistake.
        imbalance = min(1., (max(0, abs(int(counts[0])-int(counts[1]))-1)/2.)**2) if moving else 0.
        if moving and measured:
            self.window_balance_time += dt
            self.window_balance_integral += imbalance*dt
            self.repeat_count += repeat
        n = max(1, self.i_n)
        return {'pitch_rate_sq': float(self.i_gyro_sq[1]/n),
                'roll_rate_sq': float(self.i_gyro_sq[0]/n),
                'pitch_excursion_cost': float(self.i_pitch_excess/n),
                'impact_load_cost': float(self.i_load_excess/n),
                'touchdown_speed_cost': float(self.i_touchdown_cost),
                'recent_step_imbalance_cost': float(imbalance),
                'repeated_landing_events': int(repeat if moving else 0),
                'peak_loads_N': self.i_load_peak.copy(),
                'touchdown_down_speed_m_s': self.i_td_speed_peak.copy(),
                'raw_touchdowns': self.i_touchdowns.copy(),
                'quality_sample_count': int(self.i_n)}

    def summary(self) -> dict:
        n, a = max(1, self.n), max(1, self.action_n)
        pitch_std = max(0., self.pitch_sq/n-(self.pitch_sum/n)**2)**.5
        return {'quality_measurement': 'physics_substeps', 'quality_samples': int(self.n),
                'body_weight_N': self.bw,
                'pitch_rate_rms_rad_s': float((self.gyro_sq[1]/n)**.5),
                'roll_rate_rms_rad_s': float((self.gyro_sq[0]/n)**.5),
                'yaw_rate_rms_rad_s': float((self.gyro_sq[2]/n)**.5),
                'pitch_rate_peak_rad_s': float(self.gyro_peak[1]),
                'body_pitch_std_deg': float(np.rad2deg(pitch_std)),
                'body_pitch_peak_to_peak_deg': float(np.rad2deg(self.pitch_max-self.pitch_min)) if self.n else 0.,
                'body_pitch_abs_max_deg': float(np.rad2deg(max(abs(self.pitch_min), abs(self.pitch_max)))) if self.n else 0.,
                'peak_sole_load_N': self.load_peak.tolist(),
                'peak_sole_load_bw': (self.load_peak/self.bw).tolist(),
                'mean_excess_load_cost': float(self.load_excess_sum/n),
                'raw_touchdown_counts': self.touchdowns.tolist(),
                'touchdown_speed_rms_m_s': np.sqrt(self.td_speed_sq/np.maximum(1, self.touchdowns)).tolist(),
                'touchdown_speed_peak_m_s': self.td_speed_peak.tolist(),
                'action_delta_rms': float((self.action_delta_sq/a)**.5),
                'action_second_difference_rms': float((self.action_delta2_sq/a)**.5),
                'target_error_rms_rad': np.sqrt(self.target_error_sq/a).tolist(),
                'mean_recent_step_imbalance_cost': float(self.window_balance_integral/max(.02, self.window_balance_time)),
                'repeated_valid_landings': int(self.repeat_count)}


def quality_checks(s: dict, cfg: dict) -> dict[str, bool]:
    """Separate experimental quality gates, not hardware safety ratings."""
    if cfg['env']['walk_objective_version'] not in (3, 4) or s['requested_forward_m_s'] <= .003:
        return {}
    c = cfg['success']
    forward = s.get('forward_landings', [0, 0])
    # A difference of one at a time-limit boundary is not an asymmetry failure.
    excess = max(0, abs(forward[0]-forward[1])-1)/max(1, sum(forward))
    seq = s.get('landing_sequence', [])
    repeats = sum(a == b for a, b in zip(seq, seq[1:]))/max(1, len(seq)-1)
    has = bool(s.get('quality_samples', 0) > 0)
    checks = {'quality_measured': has,
            'pitch_rate': has and s.get('pitch_rate_rms_rad_s', math.inf) <= c['refine_max_pitch_rate_rms_rad_s'],
            'pitch_excursion': has and s.get('body_pitch_peak_to_peak_deg', math.inf) <= c['refine_max_pitch_peak_to_peak_deg'],
            'action_smoothness': has and s.get('action_delta_rms', math.inf) <= c['refine_max_action_delta_rms'],
            'step_balance': min(forward) >= 2 and excess <= c['refine_max_step_excess_fraction'],
            'step_alternation': len(seq) >= 4 and repeats <= c['refine_max_repeat_fraction'],
            'load_peak': has and max(s.get('peak_sole_load_bw', [math.inf])) <= c['refine_max_load_bw']}
    if cfg['env']['walk_objective_version'] == 4:
        distance = s.get('commanded_distance_m', 0.)
        ratio = s.get('forward_m', 0.)/distance if distance > 1e-9 else math.inf
        checks.update({
            'distance_tracking': c['refine_distance_ratio_min'] <= ratio <= c['refine_distance_ratio_max'],
            'mean_velocity_tracking': s.get('mean_abs_forward_velocity_error_m_s', math.inf) <= c['refine_max_velocity_error_m_s'],
            'target_smoothness': s.get('target_metric_samples', 0) > 0 and s.get('target_delta_rms_rad_mean', math.inf) <= c['refine_max_target_delta_rms_rad'],
        })
    return checks


def quality_score(s: dict) -> float:
    """Bounded ranking score. Must be gated by real locomotion by the caller."""
    if s.get('quality_samples', 0) <= 0:
        return 0.
    counts = s.get('forward_landings', [0, 0])
    balance = max(0, abs(counts[0]-counts[1])-1)/max(1, sum(counts))
    terms = [s['pitch_rate_rms_rad_s']/1., s['action_delta_rms']/.25,
             s.get('mean_excess_load_cost', 0.)**.5,
             s.get('body_pitch_peak_to_peak_deg', 0.)/25., balance*2.]
    return float(np.mean(np.exp(-np.minimum(np.square(terms), 80.))))


def quality_score_v4(s: dict) -> float:
    """Reward-independent ordering AFTER basic locomotion. No speed reward.

    Distance overshoot and undershoot are symmetric. Actual contact sequence,
    not credited events, determines repetition. Raw actions remain separate
    from smoothed servo targets. All terms are finite bounded [0,1].
    """
    if s.get("quality_samples", 0) <= 0 or s.get("target_metric_samples", 0) <= 0:
        return 0.0
    c = s.get("quality_scoring_limits", {})
    ratio = s.get("forward_m", 0.)/max(1e-9, s.get("commanded_distance_m", 0.))
    seq = s.get("landing_sequence", [])
    repeat = sum(a == b for a, b in zip(seq, seq[1:]))/max(1, len(seq)-1)
    forward = s.get("forward_landings", [0, 0])
    imbalance = max(0, abs(forward[0]-forward[1])-1)/max(1, sum(forward))
    terms = [
        s.get("action_delta_rms", math.inf)/c.get("refine_max_action_delta_rms", .25),
        s.get("target_delta_rms_rad_mean", math.inf)/c.get("refine_max_target_delta_rms_rad", .0125),
        repeat/c.get("refine_max_repeat_fraction", .25),
        abs(ratio-1.)/max(1e-6, c.get("refine_distance_ratio_max", 1.10)-1.),
        s.get("mean_abs_forward_velocity_error_m_s", math.inf)/c.get("refine_max_velocity_error_m_s", .012),
        s.get("pitch_rate_rms_rad_s", math.inf)/c.get("refine_max_pitch_rate_rms_rad_s", 1.),
        imbalance/c.get("refine_max_step_excess_fraction", .2),
    ]
    return float(np.mean(np.exp(-np.minimum(np.square(terms), 80.))))
