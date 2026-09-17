#!/usr/bin/env python3
"""Recreate the unit-test report; skips are never counted as executed passes."""
from pathlib import Path
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from stackchan_rl.checkpoints import versions
from stackchan_rl.config import load_config
from stackchan_rl.spec import RobotSpec


def main():
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"))
    out = ROOT / "validation"
    with (out / "unit_tests.log").open("w", encoding="utf-8") as log:
        result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
    spec = RobotSpec.load(load_config(ROOT / "configs/stand.json"))
    skipped = [{"test": test.id(), "reason": reason} for test,reason in result.skipped]
    report = {
        "scope": "software unit tests; not a learned-policy success report",
        "discovered": result.testsRun,
        "passed_executed": result.testsRun-len(result.skipped)-len(result.errors)-len(result.failures),
        "skipped": skipped,
        "errors": [{"test": t.id(), "traceback": tb} for t,tb in result.errors],
        "failures": [{"test": t.id(), "traceback": tb} for t,tb in result.failures],
        "versions": versions(),
        "model_name": spec.name,
        "model_mass_kg": spec.mass,
        "model_fingerprint": spec.fingerprint,
        "runtime_tests_all_executed_without_error": not skipped and result.wasSuccessful(),
        "standing_or_walking_success_claimed": False,
    }
    (out / "unit_tests.json").write_text(json.dumps(report, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    print(f"executed passes={report['passed_executed']}; skipped={len(skipped)}; failures={len(result.failures)}; errors={len(result.errors)}")
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    raise SystemExit(main())
