"""Rate rewards integrate over dt. Discrete landing/failure rewards do not.
No positive reward at termination. v2 progress shaping is distinct from the
independent success checks, which require measured steps as well as forward travel.
"""
from __future__ import annotations
import numpy as np


def _legacy_reward_terms(s: dict, w: dict, task: str, dt: float, terminated: bool) -> dict[str, float]:
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



def reward_terms(s: dict, w: dict, task: str, dt: float, terminated: bool) -> dict[str, float]:
    """Versioned reward: old checkpoints retain the old objective on replay.

    v2's velocity reward has exactly zero credit for zero speed under a positive
    command. Landing/liftoff bonuses are measured, debounced discrete events;
    progress is new body high-water distance, not abs(displacement).
    """
    result = _legacy_reward_terms(s, w, task, dt, terminated)
    if terminated or task != "walk" or s.get("walk_objective_version", 1) != 2:
        return result
    for k in ("forward_progress", "unload", "liftoff_event", "forward_landing_event",
              "alternating_event", "no_step", "overspeed"):
        result[k] = 0.0
    moving = s["command"][0] > 0.003
    if not moving:
        return result
    cmd = float(s["command"][0])
    requested = max(float(s.get("requested_forward_m_s", cmd)), 0.003)
    sigma = max(w["velocity_min_sigma_m_s"], w["velocity_relative_sigma"]*cmd)
    error = s["velocity"][:2]-s["command"][:2]
    baseline = float(np.exp(-min(80., cmd*cmd/(sigma*sigma))))
    matching = float(np.exp(-min(80., float(error@error)/(sigma*sigma))))
    relative = float(np.clip((matching-baseline)/max(1e-6, 1-baseline), -1., 1.))
    result["velocity"] = w["velocity"] * relative * dt
    # No forward-position anchoring while walking. Lateral drift is still costly.
    result["position"] = -w["position"]*min(4., (float(s["position_error"][1])/0.03)**2)*dt
    new_distance = max(0., float(s.get("new_forward_distance_m", 0.)))
    result["forward_progress"] = w["forward_progress"] * min(new_distance/requested, 2*dt)
    result["overspeed"] = -w["overspeed"] * min(4., max(0., float(s["velocity"][0])/requested-1.5)**2)*dt

    swing = np.asarray(s["swing_mask"], dtype=bool)
    contacts = np.asarray(s["contacts"], dtype=bool)
    # v1 gave an always-grounded policy half credit during swing. v2 requires
    # the full contact pair to match the phase; double support is only a phase.
    result["gait_contact"] = w["gait_contact"]*float(np.array_equal(contacts, ~swing))*dt
    result["clearance"] = 0.
    if int(np.sum(swing)) == 1:
        i = int(np.flatnonzero(swing)[0]); j = 1-i
        supported = float(contacts[j])
        loads = np.maximum(0., np.asarray(s.get("loads", [0., 0.]), dtype=float))
        share = float(loads[i]/max(1e-6, loads.sum()))
        result["unload"] = w["unload"] * supported * float(np.clip(1.-2.*share, 0., 1.))*dt
        h = max(0., float(s["foot_height"][i]))
        target = w["target_clearance_m"]
        lift = min(1., h/target) * float(np.exp(-min(80., (max(0., h-target)/target)**2)))
        result["clearance"] = w["clearance"] * supported * float(not contacts[i]) * lift * dt
    # Bounded penalty, not a new termination. Ending an episode on stagnation
    # can teach deliberate falls to escape a negative tail of rewards.
    age = s.get("no_step_elapsed_s", 0.)
    grace, ramp = s.get("no_step_grace_s", 1.5), s.get("no_step_ramp_s", 1.)
    result["no_step"] = -w["no_step"]*float(np.clip((age-grace)/ramp, 0., 1.))*dt
    result["liftoff_event"] = w["liftoff_event"]*s.get("rewarded_liftoffs_this_step", 0)
    result["landing_event"] = w["landing_event"]*s.get("rewarded_landings_this_step", 0)
    result["forward_landing_event"] = w["forward_landing_event"]*s.get("forward_landings_this_step", 0)
    result["alternating_event"] = w["alternating_event"]*s.get("alternating_landings_this_step", 0)
    return {k: float(v) for k, v in result.items()}

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
            "forward_progress": summary["forward_m"] >= max(c.get("walk_min_forward_m", 0.025), c["walk_min_command_distance_fraction"] * summary["commanded_distance_m"]),
            "lateral_drift": abs(summary["lateral_m"]) <= c["walk_max_lateral_m"],
            "heading": summary["max_heading_deg"] <= c["walk_max_heading_deg"],
            "velocity_tracking": summary["mean_abs_forward_velocity_error_m_s"] <= c["walk_velocity_error_m_s"],
            "real_steps_both_feet": min(summary["valid_landings"]) >= c["walk_min_landings_each"],
            "alternating_steps": alternating >= c.get("walk_min_alternations", 3),
            "advancing_steps_both_feet": min(summary.get("forward_landings", [0, 0])) >= c.get("walk_min_forward_landings_each", 0),
            "not_flight_or_hopping_only": summary["flight_fraction"] <= c["walk_max_flight_fraction"]}
