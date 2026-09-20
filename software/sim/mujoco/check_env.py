#!/usr/bin/env python3
"""Fail-fast contract/API checks plus a zero-action PD baseline.

A PASS_ENVIRONMENT result means the interface works, NOT that the robot stands.
The separate pd_baseline section reports observed survival and failure reason.
"""
from __future__ import annotations
import argparse
from copy import deepcopy
from pathlib import Path
import traceback


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", type=Path, default=Path(__file__).parent / "configs/stand.json")
    p.add_argument("--seconds", type=float, default=10.0)
    p.add_argument("--out", type=Path, default=Path("outputs/preflight.json"))
    p.add_argument("--skip-visual-model", action="store_true", help="skip compiling the full visual-mesh model")
    args = p.parse_args()
    if args.seconds <= 0:
        p.error("seconds must be positive")
    from stackchan_rl.config import load_config, save_json
    from stackchan_rl.spec import RobotSpec, JOINT_NAMES, OBS_DIM
    from stackchan_rl.checkpoints import versions
    cfg = load_config(args.config)
    spec = RobotSpec.load(cfg)
    result = {"status": "STARTING", "versions": versions(), "model": spec.name,
              "mass_kg": spec.mass, "model_fingerprint": spec.fingerprint,
              "physics_executed": False, "observation_dim": OBS_DIM, "action_dim": 10}
    try:
        import numpy as np
        import mujoco
        from stable_baselines3.common.env_checker import check_env
        from stackchan_rl.env import StackChanEnv
    except ImportError as exc:
        result.update(status="NOT_RUN_MISSING_DEPENDENCIES", error=str(exc),
                      install="python -m pip install -r requirements.txt")
        save_json(args.out, result)
        print(result)
        return 2
    env = None
    try:
        env = StackChanEnv(cfg)
        obs1, _ = env.reset(seed=123)
        step1 = env.step(np.zeros(10, dtype=np.float32))
        obs2, _ = env.reset(seed=123)
        step2 = env.step(np.zeros(10, dtype=np.float32))
        assert np.allclose(obs1, obs2, atol=1e-7)
        assert np.allclose(step1[0], step2[0], atol=1e-6)
        assert np.isclose(step1[1], step2[1])
        result["deterministic_reset_and_step"] = "PASS"
        result["physics_executed"] = True
        check_env(env, warn=True, skip_render_check=True)
        result["sb3_check_env"] = "PASS"
        result["resolved_joints"] = [
            {"name": name, "qposadr": int(qa), "dofadr": int(va), "actuator_id": int(ai)}
            for name, qa, va, ai in zip(JOINT_NAMES, env.qadr, env.vadr, env.aidx)]
        if not args.skip_visual_model:
            env.reset(seed=123, options={"no_noise": True, "domain_randomization": False})
            full = mujoco.MjModel.from_xml_string(spec.runtime_xml(visuals=True))
            for key in ("body_mass", "body_inertia", "body_ipos", "body_iquat", "body_pos", "jnt_pos", "jnt_axis", "jnt_range", "actuator_gear", "actuator_ctrlrange", "dof_armature", "dof_damping", "dof_frictionloss"):
                assert np.allclose(getattr(full, key), getattr(env.model, key)), key
            for gid in range(env.model.ngeom):
                g = env.model.geom(gid)
                fg = full.geom(g.name)
                for attr in ("geom_pos", "geom_quat", "geom_size", "geom_contype", "geom_conaffinity", "geom_friction"):
                    assert np.allclose(getattr(env.model, attr)[gid], getattr(full, attr)[fg.id]), (g.name, attr)
            result["visual_headless_physics_equivalence"] = "PASS"
        env.close()
        baseline_cfg = deepcopy(cfg)
        baseline_cfg["env"]["episode_seconds"] = args.seconds
        env = StackChanEnv(baseline_cfg)
        env.reset(seed=7, options={"no_noise": True, "domain_randomization": False, "command_forward_m_s": 0.0})
        result["initial_penetrations"] = env.penetrations()
        for _ in range(env.max_steps):
            _, _, term, trunc, info = env.step(np.zeros(10, dtype=np.float32))
            if term or trunc:
                result["pd_baseline"] = info["episode_summary"]
                break
        result["status"] = "PASS_ENVIRONMENT"
        result["meaning"] = "Model/API/runtime connectivity passed. Baseline survival and learned-policy success are separate."
        save_json(args.out, result)
        s = result["pd_baseline"]
        print(f"PASS_ENVIRONMENT | nq/nv/nu={env.model.nq}/{env.model.nv}/{env.model.nu} | obs={OBS_DIM}")
        print(f"PD baseline: {s['duration_s']:.2f}s, success={s['is_success']}, reason={s['failure_reason']}")
        print(args.out.resolve())
        return 0
    except BaseException as exc:
        result.update(status="FAIL_ENVIRONMENT", error=repr(exc), traceback=traceback.format_exc())
        save_json(args.out, result)
        print(result["traceback"])
        return 1
    finally:
        if env is not None:
            env.close()

if __name__ == "__main__":
    raise SystemExit(main())
