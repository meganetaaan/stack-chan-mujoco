#!/usr/bin/env python3
"""Validate a JSON list of 20 recorded trials against the fixed 10 m protocol."""
import argparse
import json
from pathlib import Path
from stackchan_rl.acceptance import assess_batch


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("records", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    records = json.loads(args.records.read_text())
    if not isinstance(records, list) or any(not isinstance(r, dict) for r in records):
        parser.error("records must be a JSON list of trial objects")
    result = assess_batch(records)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    print(f"{result['successful_trials']}/{result['trials']}; recorded criteria met={result['recorded_criteria_met']}")
    return 0 if result["recorded_criteria_met"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
