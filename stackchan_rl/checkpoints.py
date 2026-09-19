"""Complete, staged checkpoint bundles with replacement rollback: weights, optimizer, config and interface."""
from __future__ import annotations
import importlib.metadata
import json
import shutil
import uuid
from pathlib import Path
from .config import save_json, normalize_config
from .spec import RobotSpec


def versions() -> dict[str, str]:
    import platform
    result = {"python": platform.python_version(), "platform": platform.platform()}
    for name in ("mujoco", "gymnasium", "stable-baselines3", "numpy", "torch"):
        try:
            result[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            result[name] = "NOT_INSTALLED"
    return result


def save_bundle(agent, destination: str | Path, config: dict, interface: dict, metrics: dict | None = None) -> Path:
    destination = Path(destination).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = destination.parent / ("." + destination.name + ".tmp-" + uuid.uuid4().hex)
    backup = destination.parent / ("." + destination.name + ".previous-" + uuid.uuid4().hex)
    staging.mkdir()
    try:
        agent.save(str(staging / "model.zip"))
        save_json(staging / "config.json", config)
        save_json(staging / "interface.json", interface)
        save_json(staging / "metadata.json", {"num_timesteps": int(agent.num_timesteps),
                                             "versions": versions(), "metrics": metrics or {},
                                             "kit_version": "4.0.0", "walk_objective_version": config["env"].get("walk_objective_version", 1),
                                             "normalization": "fixed observation scales; no VecNormalize",
                                             "resume_scope": "weights + optimizer; simulator/RNG rollout state is not restored"})
        (staging / "READY").write_text("complete\n", encoding="utf-8")
        if destination.exists():
            destination.rename(backup)
        try:
            staging.rename(destination)
        except BaseException:
            if backup.exists():
                backup.rename(destination)
            raise
        if backup.exists():
            shutil.rmtree(backup)
        return destination
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def bundle_info(path: str | Path) -> tuple[Path, dict, dict, dict]:
    p = Path(path).expanduser().resolve()
    if p.is_file() and p.name == "model.zip":
        p = p.parent
    required = ("model.zip", "config.json", "interface.json", "metadata.json", "READY")
    missing = [n for n in required if not (p / n).is_file()]
    if missing:
        raise FileNotFoundError(f"Incomplete checkpoint {p}: missing {missing}. Pass the bundle directory, e.g. runs/stand/best.")
    read = lambda n: json.loads((p / n).read_text(encoding="utf-8"))
    return p, normalize_config(read("config.json")), read("interface.json"), read("metadata.json")


def assert_interface(saved: dict, config: dict) -> dict:
    current = RobotSpec.load(config).interface(config)
    if saved != current:
        differing = [k for k in set(saved) | set(current) if saved.get(k) != current.get(k)]
        raise ValueError("Checkpoint/model interface mismatch: " + ", ".join(differing) +
                         ". Do not mix A/B models or change action/observation meanings during resume.")
    return current


def assert_transfer_interface(saved: dict, config: dict, *, allow_lowpass_change: bool = False) -> tuple[dict, dict]:
    """Allow exactly the documented low-pass change, not arbitrary I/O mismatch.

    Resume/play remain strict. Used by explicit --init-from and by evaluation
    only with a dedicated opt-in flag. 61 fields and their normalization, model,
    home, slew, action scaling, and all other contract fields must match.
    """
    from copy import deepcopy
    import math
    current = RobotSpec.load(config).interface(config)
    if saved == current:
        return current, {"control_changed": False}
    if not allow_lowpass_change:
        assert_interface(saved, config)
    a, b = deepcopy(saved), deepcopy(current)
    old_tau = a.get("control", {}).pop("target_lowpass_time_constant_s", 0.0)
    new_tau = b.get("control", {}).pop("target_lowpass_time_constant_s", 0.0)
    old_kind = a.get("control", {}).pop("target_lowpass_kind", None)
    new_kind = b.get("control", {}).pop("target_lowpass_kind", None)
    for tau, kind in ((old_tau, old_kind), (new_tau, new_kind)):
        if not isinstance(tau, (float, int)) or not math.isfinite(tau) or tau < 0:
            raise ValueError("Invalid source/destination lowpass contract")
        if (tau == 0 and kind not in (None, "post_slew_v1")) or (tau > 0 and kind != "post_slew_v1"):
            raise ValueError("Unknown lowpass implementation; migration refused")
    if a != b:
        raise ValueError("Transfer mismatch beyond target lowpass; model/action/observation changes are not allowed")
    return current, {"control_changed": True, "allowed_change": "post_slew_lowpass",
                     "source_time_constant_s": old_tau, "destination_time_constant_s": new_tau,
                     "observation_note": "target field is post-filter and pre-transport-delay in the new runtime"}
