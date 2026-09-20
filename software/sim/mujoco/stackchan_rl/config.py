"""Strict JSON configuration; relative model paths are project-root relative."""
from __future__ import annotations
from copy import deepcopy
import json
from pathlib import Path
from typing import Any
import math

ROOT = Path(__file__).resolve().parent.parent
DEFAULT: dict[str, Any] = {
    "model_xml": "assets/r5a/scene.xml",
    "robot_spec": "assets/r5a/robot.json",
    "joint_map": "assets/r5a/joint_map.json",
    "task": "stand",
    "seed": 7,
    "env": {
        "policy_hz": 50,
        "episode_seconds": 10.0,
        "action_scale_rad": [0.14, 0.35, 0.45, 0.35, 0.14] * 2,
        "target_slew_rad_s": 2.0,
        # 0 preserves every v1-v3 checkpoint. Updated at physics frequency.
        "target_lowpass_time_constant_s": 0.0,
        "target_joint_margin_rad": 0.015,
        "max_outward_hip_spread_rad": math.radians(10),
        "actual_guard_margin_rad": 0.035,
        "fall_tilt_deg": 35.0,
        "min_height_ratio": 0.62,
        "max_height_ratio": 1.65,
        "max_joint_speed_rad_s": 30.0,
        "reset_tilt_deg": 2.0,
        "reset_yaw_deg": 5.0,
        "reset_joint_noise_rad": 0.007,
        "reset_joint_velocity_rad_s": 0.02,
        "reset_linear_velocity_m_s": 0.004,
        "reset_angular_velocity_rad_s": 0.02,
        "reset_clearance_m": 0.0005,
        "contact_threshold_N": 0.35,
        "bad_contact_threshold_N": 0.40,
        "self_contact_threshold_N": 0.8,
        "command_forward_range_m_s": [0.0, 0.0],
        "command_zero_probability": 1.0,
        "command_start_s": 0.5,
        "command_ramp_s": 1.0,
        "gait_period_s": 1.6,
        "minimum_airtime_s": 0.08,
        "minimum_lift_m": 0.002,
        "measurement_start_s": 0.5,
        # Added in v2; legacy bundles fill these with defaults, not new rewards.
        "walk_objective_version": 1,
        "gait_quality_metrics": False,
        "quality_window_s": 4.0,
        "touchdown_min_airtime_s": 0.04,
        "landing_contact_confirm_s": 0.04,
        "minimum_foot_advance_m": 0.004,
        "event_cooldown_s": 0.25,
        "no_step_grace_s": 1.5,
        "no_step_ramp_s": 1.0,
        "obs_clip": 10.0,
        "domain_randomization": False,
        "mass_scale_range": [0.95, 1.05],
        "friction_scale_range": [0.85, 1.15],
        "motor_strength_range": [0.90, 1.0],
    },
    "reward": {
        "alive": 0.25,
        "upright": 1.5,
        "height": 0.8,
        "velocity": 1.5,
        "heading": 0.25,
        "position": 0.5,
        "double_support": 0.25,
        "gait_contact": 0.0,
        "clearance": 0.0,
        "landing_event": 0.0,
        "pose": 0.03,
        "angular_velocity": 0.04,
        "joint_velocity": 0.004,
        "torque": 0.04,
        "power": 0.03,
        "action_rate": 0.04,
        "slip": 0.08,
        "flight": 0.25,
        "saturation": 0.06,
        "self_contact": 0.5,
        "termination": 2.0,
        "velocity_sigma_m_s": 0.035,
        "height_sigma_m": 0.015,
        "tilt_sigma_rad": 0.18,
        "target_clearance_m": 0.006,
        "velocity_relative_sigma": 0.6,
        "velocity_min_sigma_m_s": 0.006,
        "forward_progress": 0.0,
        "unload": 0.0,
        "liftoff_event": 0.0,
        "forward_landing_event": 0.0,
        "alternating_event": 0.0,
        "no_step": 0.0,
        "overspeed": 0.0,
        # v3-only costs; legacy objectives ignore these even when measured.
        "pitch_rate": 0.0,
        "pitch_excursion": 0.0,
        "action_acceleration": 0.0,
        "impact_load": 0.0,
        "touchdown_speed": 0.0,
        "step_imbalance": 0.0,
        "repeated_step": 0.0,
        "pitch_free_deg": 8.0,
        "pitch_scale_deg": 8.0,
        "impact_free_bw": 2.5,
        "overspeed_free_fraction": 0.10,
        "touchdown_free_speed_m_s": 0.05,
        "touchdown_speed_scale_m_s": 0.10,
    },
    "success": {
        "stand_max_tilt_deg": 15.0,
        "stand_max_drift_m": 0.035,
        "stand_min_double_support_fraction": 0.80,
        "walk_max_tilt_deg": 25.0,
        "walk_max_lateral_m": 0.05,
        "walk_max_heading_deg": 20.0,
        "walk_velocity_error_m_s": 0.03,
        "walk_min_command_distance_fraction": 0.5,
        "walk_min_landings_each": 2,
        "walk_max_flight_fraction": 0.15,
        "walk_min_forward_landings_each": 0,
        "walk_min_alternations": 3,
        "walk_min_forward_m": 0.025,
        "refine_max_pitch_rate_rms_rad_s": 1.0,
        "refine_max_pitch_peak_to_peak_deg": 25.0,
        "refine_max_action_delta_rms": 0.25,
        "refine_max_step_excess_fraction": 0.20,
        "refine_max_repeat_fraction": 0.25,
        "refine_max_load_bw": 4.0,
        # v4 quality gates; not applied to legacy objectives.
        "refine_distance_ratio_min": 0.90,
        "refine_distance_ratio_max": 1.10,
        "refine_max_velocity_error_m_s": 0.012,
        "refine_max_target_delta_rms_rad": 0.0125,
    },
    "ppo": {
        "learning_rate": 0.0003,
        "n_steps": 512,
        "batch_size": 256,
        "n_epochs": 10,
        "gamma": 0.995,
        "gae_lambda": 0.95,
        "clip_range": 0.2,
        "ent_coef": 0.002,
        "vf_coef": 0.5,
        "max_grad_norm": 0.5,
        "target_kl": 0.03,
        "net_arch": [128, 128],
        "log_std_init": -1.5,
    },
    "transfer": {
        "actor_only": False,
        "allow_target_lowpass_change": False,
        "evaluate_before_learning": False,
        "reset_log_std": None,
    },
    "train": {
        "num_envs": 4,
        "total_timesteps": 1000000,
        "eval_every_timesteps": 50000,
        "checkpoint_every_timesteps": 100000,
        "eval_episodes": 4,
        "eval_seed": 10000,
        "eval_forward_m_s": 0.0,
        # Empty means the legacy single-command evaluation. Explicit values are
        # evaluated separately; stop and movement scores do not mask each other.
        "eval_commands_m_s": [],
        "selection_version": 1,
    },
}


def merge(base: dict, changes: dict, prefix: str = "") -> dict:
    result = deepcopy(base)
    for key, value in changes.items():
        if key not in base:
            raise ValueError(f"Unknown configuration key: {prefix}{key}")
        if isinstance(base[key], dict):
            if not isinstance(value, dict):
                raise ValueError(f"{prefix}{key} must be an object")
            result[key] = merge(base[key], value, prefix + key + ".")
        else:
            result[key] = deepcopy(value)
    return result


def load_config(path: str | Path | None = None, _seen: set[Path] | None = None) -> dict:
    if path is None:
        return deepcopy(DEFAULT)
    path = Path(path).expanduser().resolve()
    seen = set() if _seen is None else set(_seen)
    if path in seen:
        raise ValueError(f"Cyclic extends in {path}")
    seen.add(path)
    changes = json.loads(path.read_text(encoding="utf-8"))
    parent = changes.pop("extends", None)
    base = load_config(path.parent / parent, seen) if parent else DEFAULT
    result = merge(base, changes)
    validate(result)
    return result


def resolve_path(path: str | Path) -> Path:
    p = Path(path).expanduser()
    return (p if p.is_absolute() else ROOT / p).resolve()


def validate(c: dict) -> None:
    if not isinstance(c["transfer"]["actor_only"], bool):
        raise ValueError("transfer.actor_only must be boolean")
    log_std = c["transfer"]["reset_log_std"]
    if log_std is not None and (not isinstance(log_std, (int, float)) or not math.isfinite(log_std) or not -5 <= log_std <= 0):
        raise ValueError("transfer.reset_log_std must be null or in [-5,0]")
    if c["task"] not in {"stand", "walk"}:
        raise ValueError("task must be stand or walk")
    e, p, t = c["env"], c["ppo"], c["train"]
    if e["walk_objective_version"] not in (1, 2, 3, 4) or t["selection_version"] not in (1, 2, 3, 4):
        raise ValueError("Only walk objective and selection versions 1, 2, 3 or 4 are supported")
    if not isinstance(e["gait_quality_metrics"], bool) or not isinstance(c["transfer"]["evaluate_before_learning"], bool):
        raise ValueError("gait_quality_metrics / evaluate_before_learning must be boolean")
    if e["walk_objective_version"] in (3, 4) and (c["task"] != "walk" or not e["gait_quality_metrics"] or t["selection_version"] != e["walk_objective_version"]):
        raise ValueError("walk objective v3/v4 requires walk, substep quality metrics, and matching selection version")
    if t["selection_version"] in (3, 4) and e["walk_objective_version"] != t["selection_version"]:
        raise ValueError("selection v3/v4 requires matching walk objective")
    tau = e["target_lowpass_time_constant_s"]
    if isinstance(tau, bool) or not isinstance(tau, (int, float)) or not math.isfinite(tau) or tau < 0:
        raise ValueError("env.target_lowpass_time_constant_s must be finite and nonnegative")
    if not isinstance(c["transfer"]["allow_target_lowpass_change"], bool):
        raise ValueError("transfer.allow_target_lowpass_change must be boolean")
    if not 0 < c["success"]["refine_distance_ratio_min"] < 1 < c["success"]["refine_distance_ratio_max"]:
        raise ValueError("refine distance ratio interval must bracket 1")
    for k in ("quality_window_s", "touchdown_min_airtime_s"):
        if not isinstance(e[k], (int, float)) or not math.isfinite(e[k]) or e[k] <= 0:
            raise ValueError(f"env.{k} must be finite and positive")
    for k, v in c["success"].items():
        if k.startswith("refine_") and (not isinstance(v, (int, float)) or not math.isfinite(v) or v <= 0):
            raise ValueError(f"success.{k} must be finite and positive")
    for k in ("landing_contact_confirm_s", "minimum_foot_advance_m", "event_cooldown_s",
              "no_step_grace_s", "no_step_ramp_s", "minimum_airtime_s", "minimum_lift_m"):
        if not isinstance(e[k], (int, float)) or not math.isfinite(e[k]) or e[k] <= 0:
            raise ValueError(f"env.{k} must be finite and positive")
    for k in ("velocity_relative_sigma", "velocity_min_sigma_m_s", "target_clearance_m", "pitch_scale_deg", "touchdown_speed_scale_m_s"):
        if not isinstance(c["reward"][k], (int, float)) or not math.isfinite(c["reward"][k]) or c["reward"][k] <= 0:
            raise ValueError(f"reward.{k} must be finite and positive")
    for k, v in c["reward"].items():
        if not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0:
            raise ValueError(f"reward.{k} must be finite and nonnegative")
    if not isinstance(t["eval_commands_m_s"], list) or any(not isinstance(x, (int, float)) or not math.isfinite(x) or x < 0 for x in t["eval_commands_m_s"]):
        raise ValueError("train.eval_commands_m_s must contain nonnegative finite velocities")
    if c["task"] == "stand" and any(t["eval_commands_m_s"]):
        raise ValueError("stand evaluation cannot request motion")
    for k in ("policy_hz", "episode_seconds", "target_slew_rad_s", "gait_period_s", "command_ramp_s"):
        if not isinstance(e[k], (int, float)) or e[k] <= 0 or not math.isfinite(e[k]):
            raise ValueError(f"env.{k} must be finite and positive")
    if len(e["action_scale_rad"]) != 10 or any(not math.isfinite(x) or x <= 0 for x in e["action_scale_rad"]):
        raise ValueError("action_scale_rad must contain ten positive values")
    for key in ("command_forward_range_m_s", "mass_scale_range", "friction_scale_range", "motor_strength_range"):
        v = e[key]
        if len(v) != 2 or not all(math.isfinite(x) for x in v) or v[0] < 0 or v[0] > v[1]:
            raise ValueError(f"Invalid range env.{key}")
    if min(e["mass_scale_range"] + e["friction_scale_range"] + e["motor_strength_range"]) <= 0:
        raise ValueError("Physical scale factors must be positive")
    if e["motor_strength_range"][1] > 1.0:
        raise ValueError("motor_strength_range may derate, but must not increase the source torque limits")
    if not 0 <= e["command_zero_probability"] <= 1:
        raise ValueError("command_zero_probability must be in [0,1]")
    if c["task"] == "stand" and (e["command_forward_range_m_s"] != [0.0, 0.0] or t["eval_forward_m_s"] != 0):
        raise ValueError("stand task cannot request forward velocity")
    if c["task"] == "walk" and e["command_forward_range_m_s"][1] <= 0:
        raise ValueError("walk task requires positive training commands")
    if not 0 < e["min_height_ratio"] < 1 < e["max_height_ratio"] or not 0 < e["fall_tilt_deg"] < 90:
        raise ValueError("Invalid fall thresholds")
    for k in ("num_envs", "total_timesteps", "eval_every_timesteps", "checkpoint_every_timesteps", "eval_episodes"):
        if not isinstance(t[k], int) or t[k] <= 0:
            raise ValueError(f"train.{k} must be a positive integer")
    for k in ("n_steps", "batch_size", "n_epochs"):
        if not isinstance(p[k], int) or p[k] <= 0:
            raise ValueError(f"ppo.{k} must be a positive integer")
    if p["n_steps"] * t["num_envs"] < p["batch_size"] or (p["n_steps"] * t["num_envs"]) % p["batch_size"]:
        raise ValueError("num_envs * n_steps must be divisible by batch_size")
    if not 0 < p["gamma"] < 1 or not 0 < p["gae_lambda"] <= 1:
        raise ValueError("Invalid discount / GAE")


def save_json(path: str | Path, value: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


def normalize_config(raw: dict) -> dict:
    """Fill added v2/v3 fields for old bundles without upgrading their objective.

    In particular the fallback walk_objective_version stays 1. Old PPO
    checkpoints must not silently acquire different rewards when resumed.
    """
    c = merge(DEFAULT, raw)
    validate(c)
    return c
