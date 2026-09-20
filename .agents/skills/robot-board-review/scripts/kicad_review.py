#!/usr/bin/env python3
"""Run read-only KiCad ERC/DRC; never equate a clean report with board approval.

Python 3.10+, standard library only. Exit 0: requested checks passed;
1: violations; 2: input/tool/report failure (not checked).
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Sequence

COMMANDS = {"sch": "erc", "pcb": "drc"}
SUFFIXES = {"sch": ".kicad_sch", "pcb": ".kicad_pcb"}


def run(command: list[str], timeout: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command, capture_output=True, text=True, encoding="utf-8",
        errors="replace", check=False, timeout=timeout,
    )


def command_for(cli: str, kind: str, source: Path, report: Path,
                refill: bool) -> list[str]:
    command = [cli, kind, COMMANDS[kind], "--format", "json",
               "--severity-all", "--exit-code-violations"]
    if kind == "pcb" and refill:
        command.append("--refill-zones")
    # Do not use --save-board, infer a schematic partner, or overwrite inputs.
    return command + ["--output", str(report), str(source)]


def review(args: argparse.Namespace) -> int:
    inputs: list[tuple[str, Path]] = []
    for kind, paths in (("sch", args.schematic), ("pcb", args.pcb)):
        for path in paths:
            source = Path(path).resolve(strict=True)
            if not source.is_file() or source.suffix != SUFFIXES[kind]:
                raise ValueError(f"Expected an existing {SUFFIXES[kind]} file: {path}")
            if (kind, source) not in inputs:
                inputs.append((kind, source))

    cli = shutil.which(args.kicad_cli)
    if cli is None:
        raise ValueError(f"KiCad CLI not found: {args.kicad_cli}")
    version = run([cli, "version"], args.timeout)
    if version.returncode != 0 or not version.stdout.strip():
        raise ValueError(f"Cannot read KiCad version: {version.stderr.strip()}")

    refill = False
    for kind in sorted({kind for kind, _ in inputs}):
        help_result = run([cli, kind, COMMANDS[kind], "--help"], args.timeout)
        required = ("--format", "--severity-all", "--exit-code-violations")
        if help_result.returncode != 0 or any(
            flag not in help_result.stdout for flag in required
        ):
            raise ValueError(f"Unsupported KiCad {kind} {COMMANDS[kind]} CLI options")
        if kind == "pcb":
            refill = "--refill-zones" in help_result.stdout
            if not refill and not args.zones_prefilled:
                raise ValueError(
                    "This CLI cannot refill zones. Refill and save ALL zones in a "
                    "review copy first, then explicitly pass --zones-prefilled."
                )

    parent = None
    if args.output_dir is not None:
        parent = Path(args.output_dir).resolve()
        parent.mkdir(parents=True, exist_ok=True)
    # A fresh directory prevents old reports from turning a failed run green.
    output = Path(tempfile.mkdtemp(prefix="board-review-", dir=parent))
    print(f"Reports: {output}")
    checks: list[dict] = []
    exit_code = 0
    for number, (kind, source) in enumerate(inputs, 1):
        name = f"{number:03d}-{source.stem}.{COMMANDS[kind]}"
        report = output / f"{name}.json"
        log = output / f"{name}.log"
        command = command_for(cli, kind, source, report, refill)
        entry = {
            "input": str(source), "kind": COMMANDS[kind], "command": command,
            "report": str(report), "log": str(log), "status": "NOT_CHECKED",
            "zones": ("refilled_in_memory" if refill else "prefilled_by_caller")
            if kind == "pcb" else "not_applicable",
        }
        try:
            entry["input_sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
            result = run(command, args.timeout)
            entry["returncode"] = result.returncode
            log.write_text(result.stdout + "\nSTDERR:\n" + result.stderr, encoding="utf-8")
            if result.returncode not in (0, 5):
                raise ValueError(f"KiCad execution failed (exit {result.returncode})")
            # Do not accept exit 0 without a fresh, readable JSON report.
            data = json.loads(report.read_text(encoding="utf-8"))
            if not isinstance(data, dict) or not data:
                raise ValueError("KiCad report is not a non-empty JSON object")
            if hashlib.sha256(source.read_bytes()).hexdigest() != entry["input_sha256"]:
                raise ValueError("Input changed during review; rerun on a stable snapshot")
            entry["status"] = "PASS" if result.returncode == 0 else "FAIL"
            if result.returncode == 5:
                exit_code = max(exit_code, 1)
        except (OSError, ValueError, UnicodeError, subprocess.TimeoutExpired) as exc:
            entry["error"] = str(exc)
            if not log.exists():
                log.write_text(str(exc) + "\n", encoding="utf-8")
            exit_code = 2
        checks.append(entry)
        print(f"{entry['status']}: {source}")
        if "error" in entry:
            print(f"  {entry['error']}", file=sys.stderr)

    summary = {
        "kicad_version": version.stdout.strip(), "exit_code": exit_code,
        "checks": checks,
        "scope": "Only the explicitly selected ERC/DRC runs; not manufacturing approval.",
        "manual_review_required": [
            "Project/rule settings loaded correctly, ignored rules and exclusions",
            "All sheets, libraries and project dependencies at the reviewed revision",
            "Schematic/PCB parity (NOT run by this script)",
            "Ratings, power/return paths, mechanical fit and all outline corner radii",
            "Logo/revision presence and legibility in actual fabrication output",
            "Saved zone fills and Gerber/drill output at the reviewed revision",
        ],
    }
    (output / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8",
    )
    print("Manual checklist still required; this is not board approval.")
    return exit_code


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schematic", action="append", default=[], metavar="ROOT.kicad_sch")
    parser.add_argument("--pcb", action="append", default=[], metavar="BOARD.kicad_pcb")
    parser.add_argument("--kicad-cli", default="kicad-cli", help="Executable name or path")
    parser.add_argument("--output-dir", help="Parent for a fresh report directory (default: temp)")
    parser.add_argument("--timeout", type=int, default=180, help="Per-command timeout in seconds")
    parser.add_argument("--zones-prefilled", action="store_true", help=(
        "For a CLI without --refill-zones: confirm ALL zones were refilled and "
        "saved in a review copy before running. Not a skip option."
    ))
    args = parser.parse_args(argv)
    if not args.schematic and not args.pcb:
        parser.error("Specify at least one --schematic or --pcb; no inputs is NOT a pass")
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    if args.zones_prefilled and not args.pcb:
        parser.error("--zones-prefilled requires --pcb")
    try:
        return review(args)
    except (OSError, ValueError, UnicodeError, subprocess.TimeoutExpired) as exc:
        print(f"NOT_CHECKED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
