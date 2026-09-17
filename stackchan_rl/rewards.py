"""Rate rewards integrate over dt. Discrete landing/failure rewards do not.
No positive reward for fallen-state time, or for body displacement alone.
"""
from __future__ import annotations
import numpy as np


def reward_terms(s: dict, w: dict, task: str, dt: float, terminated: bool) -> dict[str, float]:
    moving = task == "walk" and s["command"][0] > 0.003
    stationary = not moving
    exp = lambda x: float(np.exp(-min(80.0, max(0.0, float(x)))))
    vel_error = s["velocity"][:2] - s["command"][:2]
    rates = {
        "alive": w["alive"],
        "upright": w["upright"] * exp((s["tilt_rad"] / w["tilt_sigma_rad"])**2),
        "height": w["height"] * exp((s["height_error"] / w["height_sigma_m"])**2),
        "velocity": w["velocity"] * exp(np.dot(vel_error, vel_error) / w["velocity_sigma_m_s"]**2),
        "heading": w["heading"] * exp((s["heading_error"] / 0.2)**2),
        "position": w["position"] * exp(np.dot(s["position_error"], s["position_error"]) / 0.03**2),
        "double_support": w["double_support"] * float(stationary and np.all(s["contacts"])),
        "pose": -w["pose"] * float(np.mean(s["pose_normalized"]**2)),
        "angular_velocity": -w["angular_velocity"] * min(100.0, float(np.dot(s["gyro"], s["gyro"]))),
        "joint_velocity": -w["joint_velocity"] * float(np.mean(np.minimum(s["qd"]**2, 400))),
        "torque": -w["torque"] * float(s["torque_fraction_sq"]),
        "power": -w["power"] * float(s["power_W"]),
        "action_rate": -w["action_rate"] * float(np.mean(s["action_delta"]**2)),
        "slip": -w["slip"] * min(25.0, float(s["slip_speed_sq"]) / 0.02**2),
        "flight": -w["flight"] * float(not np.any(s["contacts"])),
        "saturation": -w["saturation"] * float(s["saturation"]),
        "self_contact": -w["self_contact"] * float(s["self_contact"]),
        "gait_contact": 0.0,
        "clearance": 0.0,
    }
    if moving:
        desired_contact = np.logical_not(s["swing_mask"])
        rates["gait_contact"] = w["gait_contact"] * float(np.mean(s["contacts"] == desired_contact))
        lift = np.clip(s["foot_height"] / w["target_clearance_m"], 0, 1)
        rates["clearance"] = w["clearance"] * float(np.sum(lift * s["swing_mask"]) / 2)
    # A fall receives only the failure penalty, preventing reward from a final
    # apparently-upright frame immediately before an invalid numerical state.
    if terminated:
        return {"termination": -float(w["termination"])}
    result = {k: float(v) * dt for k, v in rates.items()}
    result["landing_event"] = w["landing_event"] * float(s["valid_landings_this_step"]) if moving else 0.0
    return result


def success_checks(summary: dict, cfg: dict) -> dict[str, bool]:
    """Independent acceptance tests, not an alias for high episodic reward."""
    c = cfg["success"]
    common = {
        "full_duration": bool(summary["time_limit_reached"] and not summary["terminated"]),
        "no_bad_contacts": summary["bad_contact_steps"] == 0,
        "no_self_contacts": summary["self_contact_steps"] == 0,
        "height_preserved": summary["min_height_ratio"] >= 0.80,
    }
    moving = cfg["task"] == "walk" and summary["requested_forward_m_s"] > 0.003
    if not moving:
        return {**common,
                "tilt": summary["max_tilt_deg"] <= c["stand_max_tilt_deg"],
                "position": summary["max_horizontal_drift_m"] <= c["stand_max_drift_m"],
                "double_support": summary["double_support_fraction"] >= c["stand_min_double_support_fraction"]}
    seq = summary["landing_sequence"]
    alternating = sum(a != b for a, b in zip(seq, seq[1:]))
    return {**common,
            "tilt": summary["max_tilt_deg"] <= c["walk_max_tilt_deg"],
            "forward_progress": summary["forward_m"] >= max(0.025, c["walk_min_command_distance_fraction"] * summary["commanded_distance_m"]),
            "lateral_drift": abs(summary["lateral_m"]) <= c["walk_max_lateral_m"],
            "heading": summary["max_heading_deg"] <= c["walk_max_heading_deg"],
            "velocity_tracking": summary["mean_abs_forward_velocity_error_m_s"] <= c["walk_velocity_error_m_s"],
            "real_steps_both_feet": min(summary["valid_landings"]) >= c["walk_min_landings_each"],
            "alternating_steps": alternating >= 3,
            "not_flight_or_hopping_only": summary["flight_fraction"] <= c["walk_max_flight_fraction"]}
