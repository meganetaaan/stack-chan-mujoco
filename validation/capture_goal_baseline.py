#!/usr/bin/env python3
"""Capture an auditable diagnostic summary, never an acceptance certificate."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evaluation", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    source = json.loads(args.evaluation.read_text())
    partial = source.get("status") == "IN_PROGRESS"
    groups = source.get("results", source.get("completed_commands", []))
    episodes = [e for group in groups for e in group["episode_results"]]
    if partial:
        episodes += source["episodes_current_command"]
    if not episodes:
        parser.error("no completed episodes")
    files = sorted((ROOT / "stackchan_rl").glob("*.py"))
    files += sorted((ROOT / "assets/r5a").rglob("*"))
    files += sorted((ROOT / "configs").glob("*.json"))
    files += [ROOT / "evaluate.py", Path(__file__).resolve()]
    manifest = {str(p.relative_to(ROOT)): sha256(p) for p in files if p.is_file()}
    selected = ("seed", "requested_forward_m_s", "duration_s", "forward_m", "failure_reason",
                "valid_landings", "forward_landings", "self_contact_steps", "bad_contact_steps",
                "peak_torque_Nm", "rms_torque_Nm", "saturation_fraction", "failed_checks")
    result = {
        "scope": "Existing-controller 100-second diagnostic; NOT goal acceptance",
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "INCOMPLETE" if partial else "COMPLETE",
        "domain": "simulation", "hardware_tested": False,
        "physics_executed": source.get("physics_executed", False),
        "source_sha256": sha256(args.evaluation),
        "checkpoint_sha256": sha256(args.checkpoint / "model.zip"),
        "checkpoint_interface": json.loads((args.checkpoint / "interface.json").read_text()),
        "checkpoint_metadata": {k: v for k, v in json.loads((args.checkpoint / "metadata.json").read_text()).items()
                                if isinstance(v, (str, int, float, bool)) or v is None},
        "config": source["config"], "versions": source.get("versions"),
        "source_code_base_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "file_sha256": manifest,
        "episodes_completed": len(episodes),
        "mean_forward_m": sum(e["forward_m"] for e in episodes) / len(episodes),
        "mean_duration_s": sum(e["duration_s"] for e in episodes) / len(episodes),
        "min_forward_m": min(e["forward_m"] for e in episodes),
        "max_forward_m": max(e["forward_m"] for e in episodes),
        "max_peak_torque_Nm": {j: max(e["peak_torque_Nm"][j] for e in episodes)
                              for j in episodes[0]["peak_torque_Nm"]},
        "max_saturation_fraction": {j: max(e["saturation_fraction"][j] for e in episodes)
                                    for j in episodes[0]["saturation_fraction"]},
        "episodes": [{k: e[k] for k in selected} for e in episodes],
        "limitations": ["No first-10m crossing time", "No actuator thermal or supply model",
                        "Safety termination sampled at policy rate", "Privileged simulator observations",
                        "Checkpoint is local and is not distributed by this capture script"],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    print(f"{result['status']}: {len(episodes)} episodes -> {args.out}")


if __name__ == "__main__":
    main()
