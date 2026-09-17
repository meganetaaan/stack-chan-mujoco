#!/usr/bin/env python3
"""End-to-end runtime test: preflight -> PPO -> save/load -> resume -> transfer.

This tests the software path; 128/256 transitions do NOT train a useful gait.
"""
from __future__ import annotations
import argparse
from datetime import datetime
from pathlib import Path
import subprocess
import sys
from stackchan_rl.config import ROOT, save_json


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path, help="new output directory")
    p.add_argument("--subproc", action="store_true", help="also exercise spawn with two workers")
    args = p.parse_args()
    out = (args.out or ROOT / "runs" / ("smoke_" + datetime.now().strftime("%Y%m%d_%H%M%S"))).resolve()
    if out.exists() and any(out.iterdir()):
        p.error("Use a new --out directory")
    out.mkdir(parents=True, exist_ok=True)
    n = "2" if args.subproc else "1"
    commands = [
        ["check_env.py", "--seconds", "0.2", "--out", str(out / "preflight.json")],
        ["train.py", "--config", "configs/smoke.json", "--run-dir", str(out / "stand"), "--num-envs", n, "--no-tensorboard"],
        ["evaluate.py", "--checkpoint", str(out / "stand/final"), "--episodes", "2", "--out", str(out / "evaluation.json")],
        ["train.py", "--resume", str(out / "stand/final"), "--run-dir", str(out / "resume"), "--total-timesteps", "128", "--no-tensorboard"],
        ["train.py", "--config", "configs/walk_smoke.json", "--init-from", str(out / "stand/final"), "--run-dir", str(out / "walk"), "--num-envs", n, "--no-tensorboard"],
    ]
    records = []
    for i, command in enumerate(commands):
        cmd = [sys.executable, *command]
        print("Running:", " ".join(cmd), flush=True)
        with (out / f"stage_{i}.log").open("w", encoding="utf-8") as handle:
            status = subprocess.run(cmd, cwd=ROOT, stdout=handle, stderr=subprocess.STDOUT, check=False)
        records.append({"command": cmd, "returncode": status.returncode})
        if status.returncode:
            print((out / f"stage_{i}.log").read_text(encoding="utf-8"))
            save_json(out / "smoke_result.json", {"status": "FAIL", "stages": records, "failed_stage": i})
            return status.returncode
    save_json(out / "smoke_result.json", {"status": "PASS_SOFTWARE_PIPELINE", "stages": records,
                                          "standing_or_walking_success_claimed": False})
    print("PASS_SOFTWARE_PIPELINE (not a trained standing/walking policy):", out)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
