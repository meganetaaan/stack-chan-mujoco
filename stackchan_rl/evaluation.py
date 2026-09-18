"""Held-out physical evaluation. Model selection is separate from training reward."""
from __future__ import annotations
from collections import Counter
from copy import deepcopy
import csv
from pathlib import Path
import numpy as np
from .quality import quality_score


def classify_behavior(s: dict) -> str:
    if s.get("terminated"):
        return "terminated:"+str(s.get("failure_reason") or "unspecified")
    if s["requested_forward_m_s"] <= 0.003:
        return "stand_success" if s.get("is_success") else "stand_failed_checks"
    counts = s["valid_landings"]
    if sum(counts) == 0:
        return "moving_without_verified_steps" if abs(s["forward_m"]) > 0.015 else "no_verified_steps"
    if min(counts) == 0:
        return "one_sided_stepping"
    if s["forward_m"] < 0.025:
        return "stepping_in_place"
    if s.get("locomotion_pass") and not s.get("is_success"):
        return "walking_needs_refinement"
    return "walk_success" if s.get("is_success") else "walking_candidate_failed_checks"


def evaluate_agent(agent, config: dict, episodes: int, seed: int, command: float | None = None,
                   trajectory_dir: str | Path | None = None, no_noise: bool = False,
                   on_episode=None) -> dict:
    from .env import StackChanEnv
    if episodes <= 0:
        raise ValueError("episodes must be positive")
    cfg = deepcopy(config)
    cfg["env"]["domain_randomization"] = False
    env = StackChanEnv(cfg)
    summaries = []
    try:
        for ep in range(episodes):
            options = {"domain_randomization": False, "no_noise": no_noise}
            if command is not None:
                options["command_forward_m_s"] = command
            obs, _ = env.reset(seed=seed+ep, options=options)
            handle = writer = None
            if trajectory_dir is not None:
                folder = Path(trajectory_dir)
                folder.mkdir(parents=True, exist_ok=True)
                handle = (folder / f"episode_{ep:03d}.csv").open("w", newline="", encoding="utf-8")
                row = env.trajectory_row()
                writer = csv.DictWriter(handle, fieldnames=list(row))
                writer.writeheader()
                writer.writerow(row)
            try:
                while True:
                    action, _ = agent.predict(obs, deterministic=True)
                    obs, _, terminated, truncated, info = env.step(action)
                    if writer:
                        writer.writerow(env.trajectory_row())
                    if terminated or truncated:
                        summary = info["episode_summary"]
                        summary["seed"] = seed+ep
                        summary["episode_limit_s"] = cfg["env"]["episode_seconds"]
                        summary["no_noise"] = bool(no_noise)
                        summaries.append(summary)
                        if on_episode is not None:
                            on_episode(summary)
                        break
            finally:
                if handle:
                    handle.close()
    finally:
        env.close()
    return aggregate(summaries, config["train"]["selection_version"], physics_executed=True)


def _locomotion_score(s: dict) -> float:
    if s["requested_forward_m_s"] <= 0.003:
        return 0.
    # Progress without verified steps cannot dominate selection. Falls, flight,
    # and unsafe contacts reduce this *ranking* score; no success gate is relaxed.
    def balanced(values):
        a = np.clip(np.asarray(values, dtype=float)/2., 0., 1.)
        return float(0.6*a.min()+0.4*a.mean())
    valid = balanced(s.get("valid_landings", [0,0]))
    forward = balanced(s.get("forward_landings", [0,0]))
    progress = float(np.clip(s["forward_m"]/max(0.025, s["commanded_distance_m"]), 0., 1.))
    survival = min(1., s["duration_s"]/max(0.02, s.get("episode_limit_s", 12.)))
    flight = max(0., 1.-s.get("flight_fraction", 0.)/0.15)
    safe = 0. if s.get("bad_contact_steps",0) or s.get("self_contact_steps",0) else 1.
    advancing_gate = min(1., sum(s.get("forward_landings", [0,0]))/2.)
    return survival*flight*safe*(0.2*valid+0.3*forward+0.5*progress*advancing_gate)


def aggregate(summaries: list[dict], selection_version: int = 1, *, physics_executed: bool = False) -> dict:
    if not summaries:
        raise ValueError("No completed evaluations")
    failure_counts = Counter(s["failure_reason"] or "time_limit" for s in summaries)
    success = float(np.mean([s["is_success"] for s in summaries]))
    duration = float(np.mean([s["duration_s"] for s in summaries]))
    reward = float(np.mean([s["return"] for s in summaries]))
    key = [success, duration, reward]
    by_command = {}
    for v in sorted({s["requested_forward_m_s"] for s in summaries}):
        items = [s for s in summaries if s["requested_forward_m_s"] == v]
        by_command[f"{v:.6f}"] = {"episodes": len(items),
            "success_rate": float(np.mean([s["is_success"] for s in items])),
            "mean_forward_m": float(np.mean([s["forward_m"] for s in items]))}
    moving = [s for s in summaries if s["requested_forward_m_s"] > 0.003]
    motion_score = float(np.mean([_locomotion_score(s) for s in moving])) if moving else 0.
    if selection_version == 2:
        # Macro-average commands, so extra stop trials cannot hide a failed walk.
        per_command = [v["success_rate"] for v in by_command.values()]
        key = [min(per_command), float(np.mean(per_command)), motion_score,
               float(np.mean([min(s.get("forward_landings",[0,0])) for s in moving])) if moving else 0.,
               duration, reward]
    if selection_version == 3:
        per_command = [v["success_rate"] for v in by_command.values()]
        # Quality is allowed to rank a candidate only AFTER genuine walking.
        # This prevents selecting a motionless but extremely smooth policy.
        def gate(s):
            return bool(s.get("locomotion_pass", False) and s.get("quality_samples", 0) > 0)
        eligible = [s for s in moving if gate(s)]
        eligible_rate = len(eligible)/max(1, len(moving))
        qscore = float(np.mean([quality_score(s) for s in eligible])) if eligible else 0.
        key = [eligible_rate, min(per_command), float(np.mean(per_command)),
               qscore if eligible else motion_score,
               motion_score if eligible else 0., reward]
    measured = [s for s in summaries if s.get("quality_samples", 0) > 0]
    quality_fields = ("pitch_rate_rms_rad_s", "roll_rate_rms_rad_s", "body_pitch_peak_to_peak_deg",
                      "action_delta_rms", "action_second_difference_rms", "mean_excess_load_cost",
                      "mean_recent_step_imbalance_cost", "repeated_valid_landings")
    mean_quality = {k: float(np.mean([s[k] for s in measured])) for k in quality_fields} if measured else {}
    if measured:
        mean_quality["mean_peak_sole_load_bw"] = float(np.mean([max(s["peak_sole_load_bw"]) for s in measured]))
        mean_quality["max_peak_sole_load_bw"] = float(max(max(s["peak_sole_load_bw"]) for s in measured))
    return {
        "mean_quality": mean_quality,
        "quality_measured_episodes": len(measured),
        "locomotion_pass_rate": float(np.mean([s.get("locomotion_pass", False) for s in summaries])),
        "failed_check_counts": dict(Counter(k for s in summaries for k in s.get("failed_checks", []))),
        "physics_executed": bool(physics_executed),
        "episodes": len(summaries), "success_rate": success,
        "successful_episodes": sum(s["is_success"] for s in summaries),
        "mean_duration_s": duration, "mean_return": reward,
        "mean_forward_m": float(np.mean([s["forward_m"] for s in summaries])),
        "mean_velocity_error_m_s": float(np.mean([s["mean_abs_forward_velocity_error_m_s"] for s in summaries])),
        "mean_valid_landings": np.mean([s["valid_landings"] for s in summaries],axis=0).tolist(),
        "mean_forward_landings": np.mean([s.get("forward_landings",[0,0]) for s in summaries],axis=0).tolist(),
        "mean_qualified_liftoffs": np.mean([s.get("qualified_liftoffs",[0,0]) for s in summaries],axis=0).tolist(),
        "behavior_counts": dict(Counter(classify_behavior(s) for s in summaries)),
        "failure_counts": dict(failure_counts), "by_command": by_command,
        "selection_version": selection_version, "locomotion_score": motion_score,
        "selection_key": key, "episode_results": summaries,
    }


def evaluate_configured(agent, cfg: dict) -> dict:
    commands = cfg["train"]["eval_commands_m_s"] or [cfg["train"]["eval_forward_m_s"]]
    records = []
    for i, command in enumerate(commands):
        result = evaluate_agent(agent, cfg, cfg["train"]["eval_episodes"],
                                cfg["train"]["eval_seed"]+1000*i, command=command)
        records.extend(result["episode_results"])
    return aggregate(records, cfg["train"]["selection_version"], physics_executed=True)
