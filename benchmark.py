#!/usr/bin/env python3
"""Measure local environment steps/sec without promising a training duration."""
from __future__ import annotations
import argparse
from functools import partial
import os
from pathlib import Path
import time
for key in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ[key] = "1"


def worker(cfg):
    from stackchan_rl.env import StackChanEnv
    return StackChanEnv(cfg)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--num-envs", type=int, nargs="+", default=[1, 4, 6])
    p.add_argument("--vector-steps", type=int, default=300)
    args = p.parse_args()
    if min(args.num_envs) <= 0 or args.vector_steps <= 0:
        p.error("counts must be positive")
    import numpy as np
    from stable_baselines3.common.vec_env import DummyVecEnv, SubprocVecEnv
    from stackchan_rl.config import ROOT, load_config
    cfg = load_config(ROOT / "configs/stand.json")
    for n in args.num_envs:
        fns = [partial(worker, cfg) for _ in range(n)]
        env = DummyVecEnv(fns) if n == 1 else SubprocVecEnv(fns, start_method="spawn")
        try:
            env.seed(1)
            env.reset()
            a = np.zeros((n, 10), dtype=np.float32)
            for _ in range(20):
                env.step(a)
            t0 = time.perf_counter()
            for _ in range(args.vector_steps):
                env.step(a)
            elapsed = time.perf_counter()-t0
            sps = n*args.vector_steps/elapsed
            print(f"{n} envs: {sps:.1f} environment transitions/s; simulation-only 1M steps ~{1e6/sps/3600:.2f}h")
            print("  PPO optimization, callbacks, evaluation and rendering add time.")
        finally:
            env.close()

if __name__ == "__main__":
    from multiprocessing import freeze_support
    freeze_support()
    main()
