#!/usr/bin/env python3
"""Headless, held-out-seed evaluation with physical success criteria."""
from __future__ import annotations
import argparse
import os
from pathlib import Path
for key in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ[key] = "1"


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--checkpoint", type=Path, required=True)
    p.add_argument("--episodes", type=int, default=20, help="episodes per command")
    p.add_argument("--commands", help="comma-separated forward m/s, e.g. 0,0.02,0.04,0.06")
    p.add_argument("--seed", type=int, default=20000, help="different from training/eval checkpoint selection")
    p.add_argument("--out", type=Path, default=Path("outputs/evaluation.json"))
    p.add_argument("--trajectories", type=Path, help="optional per-episode CSV directory")
    p.add_argument("--no-noise", action="store_true", help="nominal reset diagnostic only, not a robust test")
    args = p.parse_args()
    from stable_baselines3 import PPO
    import torch
    from stackchan_rl.checkpoints import bundle_info, assert_interface, versions
    from stackchan_rl.evaluation import evaluate_agent
    from stackchan_rl.config import save_json
    torch.set_num_threads(1)
    folder, cfg, interface, _ = bundle_info(args.checkpoint)
    assert_interface(interface, cfg)
    agent = PPO.load(str(folder / "model.zip"), device="cpu")
    commands = [float(x.strip()) for x in args.commands.split(",")] if args.commands else [cfg["train"]["eval_forward_m_s"]]
    results = []
    for i, command in enumerate(commands):
        output = args.trajectories / f"cmd_{command:.3f}" if args.trajectories else None
        result = evaluate_agent(agent, cfg, args.episodes, args.seed+i*1000, command=command,
                                trajectory_dir=output, no_noise=args.no_noise)
        result["command_forward_m_s"] = command
        results.append(result)
        print(f"vx={command:.3f}: success {result['successful_episodes']}/{result['episodes']}, "
              f"survival {result['mean_duration_s']:.2f}s, forward {result['mean_forward_m']:.3f}m")
    save_json(args.out, {"checkpoint": str(folder), "task": cfg["task"], "physics_executed": True,
                         "versions": versions(), "seed": args.seed, "results": results,
                         "not_hardware_validation": True})
    print(args.out.resolve())
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
