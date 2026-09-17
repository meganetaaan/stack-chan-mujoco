"""Evaluate real contacts/progress, not just the PPO reward."""
from __future__ import annotations
from collections import Counter
from copy import deepcopy
import csv
from pathlib import Path
import numpy as np


def evaluate_agent(agent, config: dict, episodes: int, seed: int, command: float | None = None,
                   trajectory_dir: str | Path | None = None, no_noise: bool = False) -> dict:
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
                        summaries.append(summary)
                        break
            finally:
                if handle:
                    handle.close()
    finally:
        env.close()
    return aggregate(summaries)


def aggregate(summaries: list[dict]) -> dict:
    if not summaries:
        raise ValueError("No completed evaluations")
    failure_counts = Counter(s["failure_reason"] or "time_limit" for s in summaries)
    success = float(np.mean([s["is_success"] for s in summaries]))
    return {
        "physics_executed": True,
        "episodes": len(summaries),
        "success_rate": success,
        "successful_episodes": sum(s["is_success"] for s in summaries),
        "mean_duration_s": float(np.mean([s["duration_s"] for s in summaries])),
        "mean_return": float(np.mean([s["return"] for s in summaries])),
        "mean_forward_m": float(np.mean([s["forward_m"] for s in summaries])),
        "mean_velocity_error_m_s": float(np.mean([s["mean_abs_forward_velocity_error_m_s"] for s in summaries])),
        "failure_counts": dict(failure_counts),
        "selection_key": [success, float(np.mean([s["duration_s"] for s in summaries])),
                          float(np.mean([s["return"] for s in summaries]))],
        "episode_results": summaries,
    }
