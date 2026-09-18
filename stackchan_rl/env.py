"""Gymnasium environment for the exact R5-A model. No CAD package required.

Policy: 50 Hz normalized position offsets. Physics/PD: source timestep (1 ms).
The floating base is initialized at reset only, never prescribed during a rollout.
The observation contains privileged simulator velocity/contact/height information;
this first-stage policy is NOT directly transferable to hardware without estimation.
"""
from __future__ import annotations
from copy import deepcopy
import math
import numpy as np
import gymnasium as gym
from gymnasium import spaces
import mujoco
from .config import validate, normalize_config
from .spec import RobotSpec, JOINT_NAMES, SOLE_GEOMS, SOLE_SITES, OBS_DIM
from .actuation import ServoBank, bounded_target
from .math_utils import euler_quat, quat_mul, yaw_matrix, wrap_angle, command_at, swing_mask
from .rewards import reward_terms, success_checks
from .steps import FootStepTracker
from .walk_events import WalkEventTracker
from .quality import GaitQuality, body_angles, quality_checks


class StackChanEnv(gym.Env):
    metadata = {"render_modes": ["human", "rgb_array"], "render_fps": 50}

    def __init__(self, config: dict, render_mode: str | None = None):
        super().__init__()
        config = normalize_config(config)
        validate(config)
        if render_mode not in (None, "human", "rgb_array"):
            raise ValueError(f"Unsupported render_mode: {render_mode}")
        self.config = deepcopy(config)
        self.e = self.config["env"]
        self.render_mode = render_mode
        self.specification = RobotSpec.load(config)
        spec = self.specification
        self.model = mujoco.MjModel.from_xml_string(spec.runtime_xml(visuals=render_mode is not None))
        self.data = mujoco.MjData(self.model)
        self.dt = 1.0 / self.e["policy_hz"]
        self.substeps = int(round(self.dt / self.model.opt.timestep))
        if self.substeps < 1 or not np.isclose(self.substeps * self.model.opt.timestep, self.dt):
            raise ValueError("policy_hz must divide the source physics rate exactly")
        self.metadata = {**type(self).metadata, "render_fps": self.e["policy_hz"]}
        self.max_steps = int(math.ceil(self.e["episode_seconds"] / self.dt))
        if (self.model.nq, self.model.nv, self.model.nu) != (17, 16, 10):
            raise ValueError("Expected R5-A with one freejoint and ten hinges")
        self.qadr = np.array([int(self.model.joint(n).qposadr[0]) for n in JOINT_NAMES])
        self.vadr = np.array([int(self.model.joint(n).dofadr[0]) for n in JOINT_NAMES])
        self.aidx = np.array([int(self.model.actuator(n + "_motor").id) for n in JOINT_NAMES])
        self.root_qadr = int(self.model.joint("floating_base").qposadr[0])
        self.root_vadr = int(self.model.joint("floating_base").dofadr[0])
        self.base_id = int(self.model.body("base").id)
        self.floor_id = int(self.model.geom("floor").id)
        self.sole_ids = np.array([int(self.model.geom(n).id) for n in SOLE_GEOMS])
        self.site_ids = np.array([int(self.model.site(n).id) for n in SOLE_SITES])
        self.home_key = int(self.model.key("home").id)
        # Resolve home joints by addresses, not by assuming qpos[7:] ordering.
        self.home = self.model.key_qpos[self.home_key].copy()
        self.home_joints = self.home[self.qadr].copy()
        self.nominal_height = float(self.home[self.root_qadr + 2])
        self.action_scale = np.array(self.e["action_scale_rad"], dtype=float)
        self.bank = ServoBank(spec.motor, float(self.model.opt.timestep), self.e["target_slew_rad_s"])
        self._verify_motors()
        self._nom_mass = self.model.body_mass.copy()
        self._nom_inertia = self.model.body_inertia.copy()
        self._nom_friction = self.model.geom_friction.copy()
        self.action_space = spaces.Box(-1.0, 1.0, shape=(10,), dtype=np.float32)
        clip = self.e["obs_clip"]
        self.observation_space = spaces.Box(-clip, clip, shape=(OBS_DIM,), dtype=np.float32)
        self._jacp = np.zeros((3, self.model.nv))
        self._jacr = np.zeros((3, self.model.nv))
        self._force = np.zeros(6)
        self._viewer = None
        self._renderer = None
        self._has_reset = False
        self._done = True
        self.last_snapshot: dict = {}
        self.last_torque = np.zeros(10)
        self.last_action = np.zeros(10)
        self.previous_action = np.zeros(10)
        self.last_reward_terms: dict[str, float] = {}

    def _verify_motors(self) -> None:
        for n, aid, jid in zip(JOINT_NAMES, self.aidx, [self.model.joint(n).id for n in JOINT_NAMES]):
            if int(self.model.actuator_trnid[aid, 0]) != jid:
                raise ValueError(f"Actuator order/attachment mismatch: {n}")
            if not np.allclose(self.model.actuator_gear[aid], [1, 0, 0, 0, 0, 0]):
                raise ValueError(f"Non-unit motor gear: {n}")
            if not np.isclose(self.model.actuator_gainprm[aid, 0], 1) or not np.allclose(self.model.actuator_biasprm[aid], 0):
                raise ValueError(f"{n} is not a pure torque actuator. Do not apply PD twice.")
            if self.model.actuator_dyntype[aid] != mujoco.mjtDyn.mjDYN_NONE:
                raise ValueError(f"Unexpected actuator dynamics: {n}")
        if self.model.neq != 0 or np.any(self.model.body_gravcomp != 0):
            raise ValueError("Root constraints/gravity compensation are not allowed")

    def reset(self, *, seed: int | None = None, options: dict | None = None):
        super().reset(seed=seed)
        options = {} if options is None else dict(options)
        unknown = set(options) - {"command_forward_m_s", "no_noise", "domain_randomization"}
        if unknown:
            raise ValueError(f"Unknown reset options: {unknown}")
        randomize = options.get("domain_randomization", self.e["domain_randomization"])
        mass_scale = float(self.np_random.uniform(*self.e["mass_scale_range"])) if randomize else 1.0
        friction_scale = float(self.np_random.uniform(*self.e["friction_scale_range"])) if randomize else 1.0
        strength = float(self.np_random.uniform(*self.e["motor_strength_range"])) if randomize else 1.0
        # Always restore from immutable nominal values; no cumulative randomization.
        self.model.body_mass[:] = self._nom_mass * mass_scale
        self.model.body_inertia[:] = self._nom_inertia * mass_scale
        self.model.geom_friction[:] = self._nom_friction
        self.model.geom_friction[:, 0] *= friction_scale
        mujoco.mj_setConst(self.model, self.data)
        no_noise = bool(options.get("no_noise", False))
        initial_penetrations = []
        for _ in range(8):
            mujoco.mj_resetDataKeyframe(self.model, self.data, self.home_key)
            if not no_noise:
                angles = np.deg2rad(self.np_random.uniform(-1, 1, 3) *
                                    [self.e["reset_tilt_deg"], self.e["reset_tilt_deg"], self.e["reset_yaw_deg"]])
                r = self.root_qadr
                self.data.qpos[r+3:r+7] = quat_mul(euler_quat(*angles), self.home[r+3:r+7])
                self.data.qpos[self.qadr] = np.clip(
                    self.home_joints + self.np_random.uniform(-self.e["reset_joint_noise_rad"], self.e["reset_joint_noise_rad"], 10),
                    self.specification.limits[:, 0] + 0.02, self.specification.limits[:, 1] - 0.02)
                self.data.qvel[self.vadr] = self.np_random.uniform(-self.e["reset_joint_velocity_rad_s"], self.e["reset_joint_velocity_rad_s"], 10)
                v = self.root_vadr
                self.data.qvel[v:v+3] = self.np_random.uniform(-self.e["reset_linear_velocity_m_s"], self.e["reset_linear_velocity_m_s"], 3)
                self.data.qvel[v+3:v+6] = self.np_random.uniform(-self.e["reset_angular_velocity_rad_s"], self.e["reset_angular_velocity_rad_s"], 3)
            mujoco.mj_forward(self.model, self.data)
            bottom = min(self._sole_bottom(i) for i in range(2))
            # Adjust height only at reset so a tilted foot doesn't start underground.
            self.data.qpos[self.root_qadr+2] += self.e["reset_clearance_m"] - bottom
            mujoco.mj_forward(self.model, self.data)
            initial_penetrations = self.penetrations(tolerance_m=0.0005, exclude_floor=True)
            if not initial_penetrations:
                break
        if initial_penetrations:
            raise RuntimeError("Reset has >0.5 mm self-penetration in the ORIGINAL collision proxies. "
                               "Review check_env.py output; collisions are not silently disabled. " + repr(initial_penetrations[:8]))
        self.bank.reset(self.home_joints, strength=strength)
        self.steps = 0
        self.phase = 0.0
        self.previous_action = np.zeros(10)
        self.last_action = np.zeros(10)
        self.last_torque = np.zeros(10)
        self._torque_fraction_sq = self._power = self._saturation = 0.0
        self._sat_each = np.zeros(10)
        R = self.data.xmat[self.base_id].reshape(3, 3)
        self.initial_heading = float(np.arctan2(R[1, 0], R[0, 0]))
        self.heading_R = yaw_matrix(self.initial_heading)
        self.start_position = self.data.xpos[self.base_id].copy()
        self.desired_xy = self.start_position[:2].copy()
        if "command_forward_m_s" in options:
            requested = float(options["command_forward_m_s"])
        elif self.config["task"] == "stand" or self.np_random.random() < self.e["command_zero_probability"]:
            requested = 0.0
        else:
            requested = float(self.np_random.uniform(*self.e["command_forward_range_m_s"]))
        if not np.isfinite(requested) or requested < 0 or (self.config["task"] == "stand" and requested != 0):
            raise ValueError("Only nonnegative forward commands are supported; stand requires zero")
        self.requested_forward = requested
        self.command = np.zeros(3)
        self.commanded_distance = 0.0
        self.step_tracker = (WalkEventTracker(self.dt, self.e)
            if self.config["task"] == "walk" and self.e["walk_objective_version"] in (2, 3)
            else FootStepTracker(self.dt, self.e["minimum_airtime_s"], self.e["minimum_lift_m"]))
        self.valid_landings = self.step_tracker.counts
        self.landing_sequence = self.step_tracker.sequence
        self.episode_return = 0.0
        self.last_reward_terms = {}
        self.reward_sums: dict[str, float] = {}
        self.stats = {
            "samples": 0, "measured_samples": 0, "double_support": 0, "flight": 0,
            "bad_contact_steps": 0, "self_contact_steps": 0,
            "max_tilt_deg": 0.0, "max_heading_deg": 0.0, "max_horizontal_drift_m": 0.0,
            "min_height_ratio": 1.0, "velocity_abs_error_sum": 0.0,
            "peak_torque": np.zeros(10), "torque_sq_sum": np.zeros(10), "sat_sum": np.zeros(10),
        }
        self.previous_action_delta = np.zeros(10)
        self.quality = (GaitQuality(self.e, self.config["reward"],
                                   float(self.model.body_mass.sum()*np.linalg.norm(self.model.opt.gravity)))
                        if self.e["gait_quality_metrics"] else None)
        self._velocity6 = np.zeros(6)
        self._site_velocity6 = np.zeros((2, 6))
        self._quality_latest = {}
        self._has_reset = True
        self._done = False
        self._warning_counts = np.array([w.number for w in self.data.warning])
        self.last_snapshot = self._snapshot()
        self._last_observation = self._observation(self.last_snapshot)
        return self._last_observation.copy(), {"task": self.config["task"], "requested_forward_m_s": requested,
                                             "mass_scale": mass_scale, "friction_scale": friction_scale,
                                             "motor_strength": strength}

    def _sole_bottom(self, i: int) -> float:
        gid = self.sole_ids[i]
        R = self.data.geom_xmat[gid].reshape(3, 3)
        # The source sole collision geom is a box; size means half extent.
        return float(self.data.geom_xpos[gid, 2] - np.abs(R[2]) @ self.model.geom_size[gid])

    def penetrations(self, tolerance_m: float = 0.0005, exclude_floor: bool = False) -> list[dict]:
        result = []
        for c in self.data.contact[:self.data.ncon]:
            if exclude_floor and self.floor_id in (c.geom1, c.geom2):
                continue
            if c.dist < -tolerance_m:
                result.append({"geom1": self.model.geom(c.geom1).name, "geom2": self.model.geom(c.geom2).name,
                               "depth_m": float(-c.dist)})
        return result

    def _snapshot(self) -> dict:
        R = self.data.xmat[self.base_id].reshape(3, 3).copy()
        mujoco.mj_jacBody(self.model, self.data, self._jacp, self._jacr, self.base_id)
        velocity = self.heading_R.T @ (self._jacp @ self.data.qvel)
        gyro = R.T @ (self._jacr @ self.data.qvel)
        foot_xyz = self.data.site_xpos[self.site_ids].copy()
        foot_vel, foot_omega = np.zeros((2, 3)), np.zeros((2, 3))
        for i, sid in enumerate(self.site_ids):
            mujoco.mj_jacSite(self.model, self.data, self._jacp, self._jacr, int(sid))
            foot_vel[i] = self._jacp @ self.data.qvel
            foot_omega[i] = self._jacr @ self.data.qvel
        loads = np.zeros(2)
        bad_force = self_force = 0.0
        slip_sum = slip_count = 0.0
        for k in range(self.data.ncon):
            c = self.data.contact[k]
            mujoco.mj_contactForce(self.model, self.data, k, self._force)
            force_mag = float(np.linalg.norm(self._force[:3]))
            if self.floor_id in (c.geom1, c.geom2):
                other = c.geom2 if c.geom1 == self.floor_id else c.geom1
                matches = np.flatnonzero(self.sole_ids == other)
                if matches.size:
                    i = int(matches[0])
                    world_force = c.frame.reshape(3, 3).T @ self._force[:3]
                    loads[i] += abs(float(world_force[2]))
                    if force_mag > self.e["contact_threshold_N"]:
                        cp_velocity = foot_vel[i] + np.cross(foot_omega[i], c.pos - foot_xyz[i])
                        slip_sum += float(cp_velocity[:2] @ cp_velocity[:2])
                        slip_count += 1.0
                else:
                    bad_force = max(bad_force, force_mag)
            else:
                self_force = max(self_force, force_mag)
        pos = self.data.xpos[self.base_id].copy()
        ep_error = self.heading_R[:2, :2].T @ (pos[:2] - self.desired_xy)
        heading_error = wrap_angle(float(np.arctan2(R[1, 0], R[0, 0])) - self.initial_heading)
        return {
            "base_position": pos, "R": R, "gravity": R.T @ np.array([0., 0., -1.]),
            "velocity": velocity, "gyro": gyro,
            "body_roll_rad": body_angles(R)[0], "body_pitch_rad": body_angles(R)[1],
            "tilt_rad": float(np.arccos(np.clip(R[2, 2], -1, 1))),
            "heading_error": heading_error, "height_error": pos[2] - self.nominal_height,
            "height_ratio": float(pos[2] / self.nominal_height), "position_error": ep_error,
            "q": self.data.qpos[self.qadr].copy(), "qd": self.data.qvel[self.vadr].copy(),
            "foot_xyz": foot_xyz, "foot_height": np.array([self._sole_bottom(i) for i in range(2)]),
            "loads": loads, "contacts": loads > self.e["contact_threshold_N"],
            "bad_contact": bad_force > self.e["bad_contact_threshold_N"],
            "bad_contact_force_N": bad_force,
            "self_contact": self_force > self.e["self_contact_threshold_N"],
            "self_contact_force_N": self_force,
            "slip_speed_sq": slip_sum / max(1.0, slip_count),
            "command": self.command.copy(), "swing_mask": swing_mask(self.phase),
        }

    def _measure_substep_quality(self) -> None:
        """Read the just-solved mj_step stage without mj_forward/reintegration.

        MuJoCo keeps contact forces and cvel from its dynamics stage. These
        samples are solver-stage measurements (within one integration timestep
        of qpos), not a continuous-time peak/impulse guarantee.
        """
        mujoco.mj_objectVelocity(self.model, self.data, mujoco.mjtObj.mjOBJ_BODY,
                                self.base_id, self._velocity6, 0)
        # Use world angular velocity and the body's explicit frame, not an
        # API-dependent inertial/local frame for an asymmetric composite body.
        R = self.data.xmat[self.base_id].reshape(3, 3)
        gyro = R.T @ self._velocity6[:3]
        roll, pitch = body_angles(R)
        loads, down = np.zeros(2), np.zeros(2)
        for i, sid in enumerate(self.site_ids):
            mujoco.mj_objectVelocity(self.model, self.data, mujoco.mjtObj.mjOBJ_SITE,
                                    int(sid), self._site_velocity6[i], 0)
        for k in range(self.data.ncon):
            c = self.data.contact[k]
            if self.floor_id not in (c.geom1, c.geom2):
                continue
            other = c.geom2 if c.geom1 == self.floor_id else c.geom1
            if other == self.sole_ids[0]: i = 0
            elif other == self.sole_ids[1]: i = 1
            else: continue
            mujoco.mj_contactForce(self.model, self.data, k, self._force)
            world_force = c.frame.reshape(3, 3).T @ self._force[:3]
            loads[i] += abs(float(world_force[2]))
            v = self._site_velocity6[i]
            cp_v = v[3:] + np.cross(v[:3], c.pos-self.data.site_xpos[self.site_ids[i]])
            down[i] = max(down[i], -float(cp_v[2]), 0.)
        if not np.isfinite(np.r_[gyro, roll, pitch, loads, down]).all():
            raise FloatingPointError("nonfinite_substep_telemetry")
        self.quality.observe(time_s=float(self.data.time), dt=float(self.model.opt.timestep),
                             gyro=gyro, roll=roll, pitch=pitch, loads=loads, contact_down_speed=down)

    def _observation(self, s: dict) -> np.ndarray:
        moving = self.config["task"] == "walk" and self.command[0] > 0.003
        phase = np.array([np.sin(2*np.pi*self.phase), np.cos(2*np.pi*self.phase)]) if moving else np.zeros(2)
        obs = np.concatenate([
            s["gravity"], s["velocity"] * 5.0, s["gyro"] * 0.25,
            (s["q"] - self.home_joints) / self.action_scale, s["qd"] * 0.10,
            self.last_action, (self.bank.filtered - self.home_joints) / self.action_scale,
            self.command * np.array([5., 5., 0.5]),
            np.array([s["height_error"] / 0.05]), s["position_error"] / 0.10,
            np.array([np.sin(s["heading_error"]), np.cos(s["heading_error"])]),
            s["contacts"].astype(float), phase,
        ])
        if obs.shape != (OBS_DIM,) or not np.isfinite(obs).all():
            raise FloatingPointError("Non-finite or malformed observation")
        return np.clip(obs, -self.e["obs_clip"], self.e["obs_clip"]).astype(np.float32)

    def _landings(self, s: dict) -> int:
        if isinstance(self.step_tracker, WalkEventTracker):
            feet = (s["foot_xyz"]-self.start_position) @ self.heading_R
            base_forward = float((s["base_position"]-self.start_position) @ self.heading_R[:,0])
            events = self.step_tracker.update(s["contacts"], s["foot_height"], feet[:,:2],
                                             base_forward, self.command[0] > 0.003)
            s.update(events)
            return int(events["valid_landings_this_step"])
        return self.step_tracker.update(s["contacts"], s["foot_height"])

    def _failure_reason(self, s: dict) -> str | None:
        if s["bad_contact"]:
            return "non_sole_floor_contact"
        if s["self_contact"]:
            return "self_contact"
        if np.rad2deg(s["tilt_rad"]) > self.e["fall_tilt_deg"]:
            return "excessive_tilt"
        if not self.e["min_height_ratio"] <= s["height_ratio"] <= self.e["max_height_ratio"]:
            return "base_height_out_of_range"
        m = self.e["actual_guard_margin_rad"]
        if s["q"][0] - s["q"][5] > self.e["max_outward_hip_spread_rad"] + m:
            return "outward_splay_search_guard"
        if np.any(s["q"] < self.specification.limits[:, 0] - m) or np.any(s["q"] > self.specification.limits[:, 1] + m):
            return "joint_limit_overshoot"
        if np.max(np.abs(s["qd"])) > self.e["max_joint_speed_rad_s"]:
            return "joint_overspeed"
        return None

    def step(self, action: np.ndarray):
        if not self._has_reset or self._done:
            raise RuntimeError("Call reset() before step(), and after termination/truncation")
        # Reject NaNs in policy outputs instead of converting them into valid actions.
        target = bounded_target(action, self.home_joints, self.specification.limits, self.e)
        action = np.clip(np.asarray(action, dtype=float), -1.0, 1.0)
        self.previous_action = self.last_action.copy()
        previous_delta = self.previous_action_delta.copy()
        self.last_action = action.copy()
        self.command = command_at(self.steps*self.dt, self.requested_forward, self.e["command_start_s"], self.e["command_ramp_s"])
        self.desired_xy += (self.heading_R @ self.command)[:2] * self.dt
        self.commanded_distance += float(self.command[0]) * self.dt
        if self.command[0] > 0.003 and self.config["task"] == "walk":
            self.phase = (self.phase + self.dt / self.e["gait_period_s"]) % 1.0
        torque_sq, sat_each, torque_peak = np.zeros(10), np.zeros(10), np.zeros(10)
        power, cap_fraction_sq = 0.0, 0.0
        failure = None
        time_before = float(self.data.time)
        if self.quality is not None:
            self.quality.begin_interval()
        try:
            for _ in range(self.substeps):
                qd = self.data.qvel[self.vadr]
                tau, saturated, _ = self.bank.step(self.data.qpos[self.qadr], qd, target)
                self.data.ctrl[self.aidx] = tau
                self.last_torque = tau.copy()
                torque_sq += tau**2
                torque_peak = np.maximum(torque_peak, np.abs(tau))
                sat_each += saturated
                power += float(np.sum(np.abs(tau * qd)))
                cap_fraction_sq += float(np.mean((tau / self.bank.cap)**2))
                mujoco.mj_step(self.model, self.data)
                if self.quality is not None:
                    self._measure_substep_quality()
                if not np.isfinite(self.data.qpos).all() or not np.isfinite(self.data.qvel).all():
                    failure = "nonfinite_state"
                    break
            # MuJoCo may auto-reset after a bad state. A time rewind/warning is a
            # failure, not a fresh successful episode hidden inside the rollout.
            warnings = np.array([w.number for w in self.data.warning])
            if np.any(warnings > self._warning_counts):
                failure = "mujoco_warning"
            self._warning_counts = warnings
            if self.data.time < time_before + self.dt - 1e-8:
                failure = failure or "physics_time_discontinuity"
            if not failure:
                mujoco.mj_forward(self.model, self.data)
                s = self._snapshot()
                failure = self._failure_reason(s)
            else:
                s = self.last_snapshot
        except (mujoco.FatalError, FloatingPointError) as exc:
            failure = "physics_error:" + str(exc)
            s = self.last_snapshot
        self.steps += 1
        self._torque_fraction_sq = cap_fraction_sq / self.substeps
        self._power = power / self.substeps
        self._sat_each = sat_each / self.substeps
        self._saturation = float(np.mean(self._sat_each))
        new_landings = self._landings(s) if failure is None else 0
        s.update({"command": self.command.copy(), "pose_normalized": (s["q"]-self.home_joints)/self.action_scale,
                  "torque_fraction_sq": self._torque_fraction_sq, "power_W": self._power,
                  "action_delta": self.last_action-self.previous_action, "saturation": self._saturation,
                  "valid_landings_this_step": new_landings,
                  "walk_objective_version": self.e["walk_objective_version"],
                  "requested_forward_m_s": self.requested_forward,
                  "no_step_grace_s": self.e["no_step_grace_s"],
                  "no_step_ramp_s": self.e["no_step_ramp_s"]})
        action_delta = self.last_action-self.previous_action
        s["action_second_delta"] = action_delta-previous_delta
        self.previous_action_delta = action_delta.copy()
        if self.quality is not None and failure is None:
            self._quality_latest = self.quality.finish_interval(
                time_s=self.steps*self.dt, dt=self.dt,
                moving=self.config["task"] == "walk" and self.command[0] > .003,
                events=s, action_delta=action_delta, action_delta2=s["action_second_delta"],
                target_error=self.bank.filtered-s["q"])
            s["gait_quality"] = self._quality_latest
        terminated = failure is not None
        # Time limits are truncations, not terminal MDP states (SB3 bootstraps).
        truncated = self.steps >= self.max_steps and not terminated
        try:
            obs = self._observation(s)
        except FloatingPointError:
            obs = self._last_observation.copy()
            terminated, truncated, failure = True, False, "nonfinite_observation"
            # Keep episode diagnostics finite when the simulator has failed.
            s = self.last_snapshot.copy()
        terms = reward_terms(s, self.config["reward"], self.config["task"], self.dt, terminated)
        reward = float(sum(terms.values()))
        self.last_reward_terms = terms
        self.episode_return += reward
        for key, value in terms.items():
            self.reward_sums[key] = self.reward_sums.get(key, 0.0) + value
        self._update_stats(s, torque_sq / self.substeps, torque_peak)
        self._last_observation = obs.copy()
        self.last_snapshot = s
        self._done = terminated or truncated
        info = {"tilt_deg": float(np.rad2deg(s["tilt_rad"])), "forward_velocity_m_s": float(s["velocity"][0]),
                "base_height_m": float(s["base_position"][2]), "saturation_fraction": self._saturation,
                "failure_reason": failure, "reward_terms": terms}
        if self._done:
            summary = self._summary(terminated, truncated, failure)
            checks = success_checks(summary, self.config)
            summary["success_checks"] = checks
            summary["locomotion_pass"] = all(checks.values())
            summary["quality_checks"] = quality_checks(summary, self.config)
            summary["is_success"] = all(checks.values()) and all(summary["quality_checks"].values())
            summary["failed_checks"] = ([k for k, v in checks.items() if not v] +
                ["quality/"+k for k, v in summary["quality_checks"].items() if not v])
            from .evaluation import classify_behavior
            summary["behavior"] = classify_behavior(summary)
            info["is_success"] = summary["is_success"]
            info["episode_summary"] = summary
        return obs, reward, bool(terminated), bool(truncated), info

    def _update_stats(self, s: dict, torque_sq: np.ndarray, torque_peak: np.ndarray) -> None:
        st = self.stats
        st["samples"] += 1
        st["max_tilt_deg"] = max(st["max_tilt_deg"], float(np.rad2deg(s["tilt_rad"])))
        st["max_heading_deg"] = max(st["max_heading_deg"], abs(float(np.rad2deg(s["heading_error"]))))
        st["max_horizontal_drift_m"] = max(st["max_horizontal_drift_m"], float(np.linalg.norm(s["base_position"][:2]-self.start_position[:2])))
        st["min_height_ratio"] = min(st["min_height_ratio"], s["height_ratio"])
        st["bad_contact_steps"] += int(s["bad_contact"])
        st["self_contact_steps"] += int(s["self_contact"])
        st["peak_torque"] = np.maximum(st["peak_torque"], torque_peak)
        st["torque_sq_sum"] += torque_sq
        st["sat_sum"] += self._sat_each
        if self.steps*self.dt >= self.e["measurement_start_s"]:
            st["measured_samples"] += 1
            st["double_support"] += int(np.all(s["contacts"]))
            st["flight"] += int(not np.any(s["contacts"]))
            st["velocity_abs_error_sum"] += abs(float(s["velocity"][0]-self.command[0]))

    def _summary(self, terminated: bool, truncated: bool, reason: str | None) -> dict:
        st = self.stats
        count = max(1, st["measured_samples"])
        delta = self.heading_R.T @ (self.last_snapshot["base_position"]-self.start_position)
        return {
            "task": self.config["task"], "return": float(self.episode_return),
            "duration_s": self.steps*self.dt, "physics_time_s": float(self.data.time),
            "terminated": terminated, "time_limit_reached": truncated, "failure_reason": reason,
            "requested_forward_m_s": self.requested_forward, "commanded_distance_m": self.commanded_distance,
            "forward_m": float(delta[0]), "lateral_m": float(delta[1]),
            "max_tilt_deg": st["max_tilt_deg"], "max_heading_deg": st["max_heading_deg"],
            "max_horizontal_drift_m": st["max_horizontal_drift_m"], "min_height_ratio": st["min_height_ratio"],
            "double_support_fraction": st["double_support"] / count, "flight_fraction": st["flight"] / count,
            "mean_abs_forward_velocity_error_m_s": st["velocity_abs_error_sum"] / count,
            "valid_landings": self.valid_landings.tolist(), "landing_sequence": list(self.landing_sequence),
            "bad_contact_steps": st["bad_contact_steps"], "self_contact_steps": st["self_contact_steps"],
            "peak_torque_Nm": dict(zip(JOINT_NAMES, st["peak_torque"].tolist())),
            "rms_torque_Nm": dict(zip(JOINT_NAMES, np.sqrt(st["torque_sq_sum"]/max(1,st["samples"])).tolist())),
            "saturation_fraction": dict(zip(JOINT_NAMES, (st["sat_sum"]/max(1,st["samples"])).tolist())),
            "reward_components": dict(self.reward_sums),
            "walk_objective_version": self.e["walk_objective_version"],
            **(self.quality.summary() if self.quality is not None else {}),
            **(self.step_tracker.summary() if isinstance(self.step_tracker, WalkEventTracker) else {}),
        }

    def trajectory_row(self) -> dict:
        s = self.last_snapshot
        row = {"time_s": self.steps*self.dt, "base_x_m": float(s["base_position"][0]),
               "base_y_m": float(s["base_position"][1]), "base_z_m": float(s["base_position"][2]),
               "tilt_deg": float(np.rad2deg(s["tilt_rad"])), "command_vx_m_s": float(self.command[0]),
               "actual_vx_m_s": float(s["velocity"][0]), "left_load_N": float(s["loads"][0]),
               "right_load_N": float(s["loads"][1]), "left_sole_height_m": float(s["foot_height"][0]),
               "right_sole_height_m": float(s["foot_height"][1]),
               "left_contact": int(s["contacts"][0]), "right_contact": int(s["contacts"][1]),
               "left_valid_landings": int(self.valid_landings[0]),
               "right_valid_landings": int(self.valid_landings[1]),
               "gait_phase": float(self.phase),
               "no_step_elapsed_s": float(s.get("no_step_elapsed_s", 0.0))}
        if isinstance(self.step_tracker, WalkEventTracker):
            for i, side in enumerate(("left", "right")):
                row[side+"_qualified_liftoffs"] = int(self.step_tracker.liftoffs[i])
                row[side+"_forward_landings"] = int(self.step_tracker.forward_counts[i])
                row[side+"_raw_unloads"] = int(self.step_tracker.raw_unloads[i])
                row[side+"_max_clearance_m"] = float(self.step_tracker.peak_episode[i])
        row.update({"body_roll_deg": float(np.rad2deg(s["body_roll_rad"])),
                    "body_pitch_deg": float(np.rad2deg(s["body_pitch_rad"])),
                    "body_roll_rate_rad_s": float(s["gyro"][0]),
                    "body_pitch_rate_rad_s": float(s["gyro"][1]),
                    "body_yaw_rate_rad_s": float(s["gyro"][2]),
                    "action_delta_rms": float(np.sqrt(np.mean((self.last_action-self.previous_action)**2))),
                    "action_second_delta_rms": float(np.sqrt(np.mean(np.asarray(s.get("action_second_delta", np.zeros(10)))**2)))})
        if self.quality is not None:
            q = self._quality_latest
            row["substep_pitch_rate_rms_rad_s"] = float(np.sqrt(q.get("pitch_rate_sq", 0.)))
            row["substep_sample_count"] = int(q.get("quality_sample_count", 0))
            row["recent_step_imbalance_cost"] = float(q.get("recent_step_imbalance_cost", 0.))
            for i, side in enumerate(("left", "right")):
                row[side+"_peak_load_N"] = float(q.get("peak_loads_N", [0., 0.])[i])
                row[side+"_touchdown_down_speed_m_s"] = float(q.get("touchdown_down_speed_m_s", [0., 0.])[i])
        # Always include every configured component, even on the initial row.
        for name in ("velocity", "forward_progress", "unload", "clearance", "no_step", "landing_event",
                     "liftoff_event", "forward_landing_event", "alternating_event", "slip", "torque",
                     "action_rate", "pitch_rate", "pitch_excursion", "action_acceleration",
                     "impact_load", "touchdown_speed", "step_imbalance", "repeated_step"):
            row["reward_"+name] = float(getattr(self, "last_reward_terms", {}).get(name, 0.0))
        for i, n in enumerate(JOINT_NAMES):
            row[n+"_rad"] = float(s["q"][i])
            row[n+"_target_rad"] = float(self.bank.filtered[i])
            row[n+"_Nm"] = float(self.last_torque[i])
            row[n+"_action"] = float(self.last_action[i])
        return row

    def render(self):
        if self.render_mode is None:
            raise RuntimeError("Construct the environment with render_mode='human' or 'rgb_array'")
        if self.render_mode == "human":
            if self._viewer is None:
                from mujoco import viewer as mj_viewer
                self._viewer = mj_viewer.launch_passive(self.model, self.data)
                with self._viewer.lock():
                    self._viewer.cam.distance = 0.55
                    self._viewer.cam.azimuth = 135
                    self._viewer.cam.elevation = -15
                    self._viewer.opt.geomgroup[3] = 0
                    self._viewer.opt.sitegroup[4] = 0
            if self._viewer.is_running():
                with self._viewer.lock():
                    self._viewer.cam.lookat[:] = self.data.xpos[self.base_id] + [0, 0, 0.055]
                self._viewer.sync()
            return None
        if self._renderer is None:
            self._renderer = mujoco.Renderer(self.model, height=720, width=960)
        cam = mujoco.MjvCamera()
        cam.type = mujoco.mjtCamera.mjCAMERA_FREE
        cam.distance, cam.azimuth, cam.elevation = 0.55, 135, -15
        cam.lookat[:] = self.data.xpos[self.base_id] + [0, 0, 0.055]
        opt = mujoco.MjvOption()
        opt.geomgroup[3] = 0
        opt.sitegroup[4] = 0
        self._renderer.update_scene(self.data, camera=cam, scene_option=opt)
        return self._renderer.render()

    def viewer_running(self) -> bool:
        return self._viewer is None or self._viewer.is_running()

    def close(self):
        if self._viewer is not None:
            self._viewer.close()
            self._viewer = None
        if self._renderer is not None:
            self._renderer.close()
            self._renderer = None
