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
    "train": {
        "num_envs": 4,
        "total_timesteps": 1000000,
        "eval_every_timesteps": 50000,
        "checkpoint_every_timesteps": 100000,
        "eval_episodes": 4,
        "eval_seed": 10000,
        "eval_forward_m_s": 0.0,
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
    if c["task"] not in {"stand", "walk"}:
        raise ValueError("task must be stand or walk")
    e, p, t = c["env"], c["ppo"], c["train"]
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
