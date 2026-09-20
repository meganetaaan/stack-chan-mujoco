"""Goal-level acceptance, independent of training reward and source domain.

This validates recorded evidence; it does not certify that hardware was tested.
"""
from __future__ import annotations

import math

PROTOCOL = "tab5-10m-v1"
FLAGS = ("fall", "self_collision", "protective_stop", "assisted", "interrupted")


def assess_trial(record: dict) -> dict:
    failures = []
    for key in ("trial_id", "design_id", "controller_id", "evidence"):
        if not isinstance(record.get(key), str) or not record[key].strip():
            failures.append("missing_" + key)
    if record.get("domain") not in ("simulation", "hardware"):
        failures.append("invalid_domain")
    if record.get("protocol") != PROTOCOL:
        failures.append("invalid_protocol")
    values = {}
    for key in ("forward_m", "elapsed_s"):
        value = record.get(key)
        if type(value) not in (int, float) or not math.isfinite(value):
            failures.append("invalid_" + key)
        else:
            values[key] = value
    for key in FLAGS:
        if type(record.get(key)) is not bool:
            failures.append("unknown_" + key)
        elif record[key]:
            failures.append(key)
    if record.get("continuous_bipedal_walk") is not True:
        failures.append("unverified_continuous_bipedal_walk")
    distance, elapsed = values.get("forward_m"), values.get("elapsed_s")
    speed = None
    if distance is not None and distance < 10.0:
        failures.append("distance")
    if elapsed is not None:
        if elapsed <= 0:
            failures.append("nonpositive_elapsed_s")
        else:
            # Fixed 10 m course: overshoot cannot compensate for a late finish.
            speed = min(10.0, distance) / elapsed if distance is not None else None
            if speed is not None and not math.isfinite(speed):
                speed = None
                failures.append("invalid_average_speed")
            if elapsed > 100.0:
                failures.append("time_limit")
    return {"trial_id": record.get("trial_id"), "passed": not failures,
            "average_course_speed_m_s": speed, "failed_checks": failures}


def assess_batch(records: list[dict]) -> dict:
    trials = [assess_trial(r) for r in records]
    issues = []
    if len(records) != 20:
        issues.append("requires_exactly_20_trials")
    ids = [r.get("trial_id") for r in records]
    if any(not isinstance(i, str) for i in ids) or len(set(i for i in ids if isinstance(i, str))) != len(ids):
        issues.append("invalid_or_duplicate_trial_ids")
    for key in ("domain", "design_id", "controller_id", "protocol"):
        values = [r.get(key) for r in records]
        if not values or any(not isinstance(v, str) or v != values[0] for v in values):
            issues.append("inconsistent_" + key)
    passed = sum(t["passed"] for t in trials)
    meets = not issues and passed >= 18
    return {"protocol": PROTOCOL, "trials": len(records), "successful_trials": passed,
            "batch_issues": issues, "recorded_criteria_met": meets,
            "hardware_criteria_met": meets and records[0]["domain"] == "hardware",
            "evidence_note": "Record validation only; raw evidence and provenance require review.",
            "trial_results": trials}
