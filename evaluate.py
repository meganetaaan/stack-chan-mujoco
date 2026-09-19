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
    p.add_argument("--config", type=Path, help="Explicit evaluation config override; same model and policy I/O required")
    p.add_argument("--allow-target-lowpass-change", action="store_true",
                   help="Explicitly permit ONLY the lowpass control change for a --config baseline evaluation")
    p.add_argument("--episodes", type=int, default=20, help="episodes per command")
    p.add_argument("--commands", help="comma-separated forward m/s, e.g. 0,0.02,0.04,0.06")
    p.add_argument("--seed", type=int, default=20000, help="different from training/eval checkpoint selection")
    p.add_argument("--out", type=Path, default=Path("outputs/evaluation.json"))
    p.add_argument("--trajectories", type=Path, help="optional per-episode CSV directory")
    p.add_argument("--no-noise", action="store_true", help="nominal reset diagnostic only, not a robust test")
    args = p.parse_args()
    from stable_baselines3 import PPO
    import torch
    from stackchan_rl.checkpoints import bundle_info, assert_interface, assert_transfer_interface, versions
    from stackchan_rl.evaluation import evaluate_agent
    from stackchan_rl.config import save_json, load_config
    torch.set_num_threads(1)
    folder, cfg, interface, _ = bundle_info(args.checkpoint)
    assert_interface(interface, cfg)
    source_interface = interface
    if args.allow_target_lowpass_change and args.config is None:
        p.error("--allow-target-lowpass-change requires --config")
    if args.config is not None:
        cfg = load_config(args.config)
    interface, migration = assert_transfer_interface(source_interface, cfg,
                                allow_lowpass_change=args.allow_target_lowpass_change)
    agent = PPO.load(str(folder / "model.zip"), device="cpu")
    commands = [float(x.strip()) for x in args.commands.split(",")] if args.commands else (cfg["train"]["eval_commands_m_s"] or [cfg["train"]["eval_forward_m_s"]])
    results = []
    for i, command in enumerate(commands):
        output = args.trajectories / f"cmd_{command:.3f}" if args.trajectories else None
        partial = []
        def on_episode(summary):
            partial.append(summary)
            # Persist complete episodes immediately, even if later evaluation
            # is interrupted. A partial file is never called a complete report.
            save_json(args.out.with_name(args.out.stem+".partial.json"),
                      {"status": "IN_PROGRESS", "checkpoint": str(folder), "seed": args.seed,
                       "physics_executed": True, "command_forward_m_s": command,
                       "config": cfg, "completed_commands": results, "episodes_current_command": partial})
            q = summary.get("pitch_rate_rms_rad_s")
            print(f"episode={len(partial)-1} success={summary['is_success']} "
                  f"duration={summary['duration_s']:.2f}s forward={summary['forward_m']:.3f}m "
                  f"landings={summary['valid_landings']} advancing={summary.get('forward_landings')} "
                  f"failed={summary.get('failed_checks', [])} pitch_rms={q} "
                  f"raw_delta={summary.get('action_delta_rms')} "
                  f"target_delta={summary.get('target_delta_rms_rad_mean')} "
                  f"distance_ratio={summary.get('command_distance_ratio')}", flush=True)
        result = evaluate_agent(agent, cfg, args.episodes, args.seed+i*1000, command=command,
                                trajectory_dir=output, no_noise=args.no_noise, on_episode=on_episode)
        result["command_forward_m_s"] = command
        results.append(result)
        print(f"vx={command:.3f}: success {result['successful_episodes']}/{result['episodes']}, "
              f"survival {result['mean_duration_s']:.2f}s, forward {result['mean_forward_m']:.3f}m "
              f"landings={result['mean_valid_landings']} advancing={result['mean_forward_landings']} "
              f"behavior={result['behavior_counts']}")
    save_json(args.out, {"checkpoint": str(folder), "task": cfg["task"], "physics_executed": True,
                         "versions": versions(), "seed": args.seed, "results": results,
                         "config": cfg, "interface": interface, "source_interface": source_interface, "control_migration": migration, "no_noise": bool(args.no_noise),
                         "evaluation_config_override": str(args.config) if args.config else None,
                         "not_hardware_validation": True})
    partial_path = args.out.with_name(args.out.stem+".partial.json")
    if partial_path.exists():
        partial_path.unlink()
    print(args.out.resolve())
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
