#!/usr/bin/env python3
"""Play a deterministic learned policy in the actual MuJoCo simulation."""
from __future__ import annotations
import argparse
import os
from pathlib import Path
import time
for key in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ[key] = "1"


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--checkpoint", type=Path, required=True)
    p.add_argument("--command", type=float, help="forward m/s; default saved evaluation command")
    p.add_argument("--seconds", type=float, help="duration per episode")
    p.add_argument("--episodes", type=int, default=3)
    p.add_argument("--speed", type=float, default=1.0, help="GUI playback speed, not physics timestep")
    p.add_argument("--seed", type=int, default=30000)
    p.add_argument("--random-reset", action="store_true")
    p.add_argument("--headless", action="store_true")
    p.add_argument("--record", type=Path, help="write MP4 instead of opening a window")
    args = p.parse_args()
    if args.speed <= 0 or args.episodes <= 0 or (args.seconds is not None and args.seconds <= 0):
        p.error("speed, episodes and seconds must be positive")
    import torch
    from stable_baselines3 import PPO
    from stackchan_rl.checkpoints import bundle_info, assert_interface
    from stackchan_rl.env import StackChanEnv
    torch.set_num_threads(1)
    folder, cfg, interface, _ = bundle_info(args.checkpoint)
    assert_interface(interface, cfg)
    if args.seconds is not None:
        cfg["env"]["episode_seconds"] = args.seconds
    cfg["env"]["domain_randomization"] = False
    command = cfg["train"]["eval_forward_m_s"] if args.command is None else args.command
    mode = "rgb_array" if args.record else (None if args.headless else "human")
    print(f"Control LPF={cfg['env']['target_lowpass_time_constant_s']:.3f}s (saved checkpoint config)", flush=True)
    env = StackChanEnv(cfg, render_mode=mode)
    agent = PPO.load(str(folder / "model.zip"), device="cpu")
    writer = None
    if args.record:
        import imageio.v2 as imageio
        args.record.parent.mkdir(parents=True, exist_ok=True)
        writer = imageio.get_writer(str(args.record), fps=cfg["env"]["policy_hz"])
    try:
        for episode in range(args.episodes):
            obs, _ = env.reset(seed=args.seed+episode, options={"command_forward_m_s": command,
                                      "no_noise": not args.random_reset, "domain_randomization": False})
            if mode == "human":
                env.render()
            deadline = time.perf_counter()
            while True:
                if not env.viewer_running():
                    return 0
                action, _ = agent.predict(obs, deterministic=True)
                obs, _, term, trunc, info = env.step(action)
                if mode == "human":
                    env.render()
                    deadline += env.dt / args.speed
                    time.sleep(max(0.0, deadline-time.perf_counter()))
                elif writer:
                    writer.append_data(env.render())
                if term or trunc:
                    s = info["episode_summary"]
                    print(f"episode={episode} success={s['is_success']} duration={s['duration_s']:.2f}s "
                          f"forward={s['forward_m']:.3f}m landings={s['valid_landings']} "
                          f"forward_landings={s.get('forward_landings', 'legacy')} "
                          f"behavior={s.get('behavior','legacy')} reason={s['failure_reason']} "
                          f"failed={s.get('failed_checks', [])} pitch_rms={s.get('pitch_rate_rms_rad_s', 'not_measured')}")
                    break
    finally:
        env.close()
        if writer:
            writer.close()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
