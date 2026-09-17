"""PPO orchestration. Import heavyweight dependencies after argument parsing."""
from __future__ import annotations
import argparse
from collections import deque
from copy import deepcopy
from functools import partial
import json
from pathlib import Path
import traceback
from .config import ROOT, load_config, validate, save_json
from .checkpoints import versions, bundle_info, assert_interface, save_bundle
from .spec import RobotSpec


def make_worker(config: dict, rank: int, log_dir: str):
    from stable_baselines3.common.monitor import Monitor
    from .env import StackChanEnv
    env = StackChanEnv(config)
    return Monitor(env, filename=str(Path(log_dir) / f"env_{rank:02d}"), override_existing=False)


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Train R5-A with CPU MuJoCo + Gymnasium + SB3 PPO")
    select = p.add_mutually_exclusive_group()
    select.add_argument("--config", type=Path, help="JSON config (default configs/stand.json)")
    select.add_argument("--task", choices=("stand", "walk"), help="shorthand for configs/<task>.json")
    source = p.add_mutually_exclusive_group()
    source.add_argument("--resume", type=Path, help="resume a complete checkpoint, including optimizer")
    source.add_argument("--init-from", type=Path, help="copy policy/value weights, NEW optimizer (e.g. stand -> walk)")
    p.add_argument("--run-dir", type=Path, required=True)
    p.add_argument("--num-envs", type=int)
    p.add_argument("--total-timesteps", type=int, help="ADDITIONAL environment transitions on resume")
    p.add_argument("--seed", type=int)
    p.add_argument("--vec", choices=("auto", "dummy", "subproc"), default="auto")
    p.add_argument("--no-tensorboard", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    resume_data = bundle_info(args.resume) if args.resume else None
    if resume_data and (args.config or args.task):
        raise ValueError("--resume uses the saved config. Use --init-from with --task walk to change task.")
    cfg = deepcopy(resume_data[1]) if resume_data else load_config(args.config or ROOT / "configs" / f"{args.task or 'stand'}.json")
    if args.num_envs is not None:
        cfg["train"]["num_envs"] = args.num_envs
    if args.total_timesteps is not None:
        cfg["train"]["total_timesteps"] = args.total_timesteps
    if args.seed is not None:
        cfg["seed"] = args.seed
    validate(cfg)
    run_dir = args.run_dir.expanduser().resolve()
    if run_dir.exists() and any(run_dir.iterdir()) and not resume_data:
        raise FileExistsError(f"{run_dir} is not empty. Use a new --run-dir, or --resume; files will not be overwritten.")
    if resume_data and (run_dir / "config.json").is_file():
        old = json.loads((run_dir / "config.json").read_text(encoding="utf-8"))
        if any(old.get(k) != cfg[k] for k in ("task", "env", "reward", "success")):
            raise ValueError("Existing run-dir belongs to a different task/environment. Resume into a new directory.")
    try:
        import torch
        from torch import nn
        from stable_baselines3 import PPO
        from stable_baselines3.common.callbacks import BaseCallback
        from stable_baselines3.common.vec_env import DummyVecEnv, SubprocVecEnv
        from .env import StackChanEnv
        from .evaluation import evaluate_agent
    except ImportError as exc:
        raise SystemExit("Missing runtime dependencies. Run: python -m pip install -r requirements.txt\n" + str(exc))
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    # Compile + reset once before spawning, so model mistakes don't create a wall
    # of child-process EOFError messages. No GUI/OpenGL context is created here.
    probe = StackChanEnv(cfg)
    try:
        probe.reset(seed=cfg["seed"], options={"no_noise": True, "domain_randomization": False})
        interface = probe.specification.interface(cfg)
    finally:
        probe.close()
    if resume_data:
        assert_interface(resume_data[2], cfg)
    init_data = bundle_info(args.init_from) if args.init_from else None
    if init_data:
        assert_interface(init_data[2], cfg)
        if init_data[1]["ppo"]["net_arch"] != cfg["ppo"]["net_arch"]:
            raise ValueError("--init-from requires the same net_arch as the saved policy")
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "monitor").mkdir(exist_ok=True)
    save_json(run_dir / "config.json", cfg)
    save_json(run_dir / "interface.json", interface)
    save_json(run_dir / "environment.json", versions())
    save_json(run_dir / "training_status.json", {"status": "STARTING", "physics_executed": False, "model_compiled": True,
                                                "task": cfg["task"], "assistance": "none"})
    fns = [partial(make_worker, cfg, i, str(run_dir / "monitor")) for i in range(cfg["train"]["num_envs"])]
    use_subproc = args.vec == "subproc" or (args.vec == "auto" and len(fns) > 1)
    vec = None
    agent = None

    class RunCallback(BaseCallback):
        def __init__(self):
            super().__init__(verbose=0)
            self.best_key = (-float("inf"),) * 3
            if resume_data:
                self.best_key = tuple(resume_data[3].get("metrics", {}).get("selection_key", self.best_key))
            if (run_dir / "best" / "READY").is_file():
                prior = bundle_info(run_dir / "best")
                assert_interface(prior[2], cfg)
                previous_best = tuple(prior[3].get("metrics", {}).get("selection_key", self.best_key))
                self.best_key = max(self.best_key, previous_best)
            self.recent = deque(maxlen=100)
            self.ep_file = None
            self.last_metrics = {}
            self.has_recorded_physics = False

        def _on_training_start(self):
            t = int(self.model.num_timesteps)
            self.next_eval = (t // cfg["train"]["eval_every_timesteps"] + 1) * cfg["train"]["eval_every_timesteps"]
            self.next_save = (t // cfg["train"]["checkpoint_every_timesteps"] + 1) * cfg["train"]["checkpoint_every_timesteps"]
            self.ep_file = (run_dir / "training_episodes.jsonl").open("a", encoding="utf-8")

        def _on_step(self) -> bool:
            if not self.has_recorded_physics:
                save_json(run_dir / "training_status.json", {"status": "TRAINING_RUNNING", "physics_executed": True,
                          "task": cfg["task"], "assistance": "none", "first_observed_timesteps": int(self.num_timesteps)})
                self.has_recorded_physics = True
            for info in self.locals.get("infos", []):
                if "episode_summary" in info:
                    s = info["episode_summary"]
                    self.recent.append(s)
                    compact = {k: s[k] for k in ("return", "duration_s", "is_success", "failure_reason", "forward_m", "max_tilt_deg", "valid_landings")}
                    compact["num_timesteps"] = int(self.num_timesteps)
                    self.ep_file.write(json.dumps(compact) + "\n")
            if self.num_timesteps >= self.next_eval:
                self.next_eval += cfg["train"]["eval_every_timesteps"]
                metrics = evaluate_agent(self.model, cfg, cfg["train"]["eval_episodes"], cfg["train"]["eval_seed"],
                                         command=cfg["train"]["eval_forward_m_s"])
                self.last_metrics = metrics
                save_json(run_dir / "evaluations" / f"step_{self.num_timesteps:010d}.json", metrics)
                self.logger.record("eval/success_rate", metrics["success_rate"])
                self.logger.record("eval/mean_duration_s", metrics["mean_duration_s"])
                self.logger.record("eval/forward_m", metrics["mean_forward_m"])
                self.logger.record("eval/mean_return", metrics["mean_return"])
                key = tuple(metrics["selection_key"])
                if key > self.best_key:
                    self.best_key = key
                    save_bundle(self.model, run_dir / "best", cfg, interface, metrics)
                print(f"[eval {self.num_timesteps}] success={metrics['successful_episodes']}/{metrics['episodes']} "
                      f"survival={metrics['mean_duration_s']:.2f}s forward={metrics['mean_forward_m']:.3f}m", flush=True)
            if self.num_timesteps >= self.next_save:
                self.next_save += cfg["train"]["checkpoint_every_timesteps"]
                save_bundle(self.model, run_dir / "checkpoints" / f"step_{self.num_timesteps:010d}", cfg, interface, self.last_metrics)
                save_bundle(self.model, run_dir / "latest", cfg, interface, self.last_metrics)
                self.ep_file.flush()
            return True

        def _on_rollout_end(self):
            if self.recent:
                for key in ("duration_s", "is_success", "max_tilt_deg", "forward_m"):
                    self.logger.record("robot/" + key, sum(float(s[key]) for s in self.recent) / len(self.recent))
                names = set().union(*(s["reward_components"] for s in self.recent))
                for name in names:
                    self.logger.record("reward_per_second/"+name, sum(s["reward_components"].get(name, 0)/max(s["duration_s"], 0.02) for s in self.recent) / len(self.recent))

        def close(self):
            if self.ep_file:
                self.ep_file.close()
                self.ep_file = None

    callback = RunCallback()
    try:
        vec = SubprocVecEnv(fns, start_method="spawn") if use_subproc else DummyVecEnv(fns)
        vec.seed(cfg["seed"])
        if resume_data:
            agent = PPO.load(str(resume_data[0] / "model.zip"), env=vec, device="cpu", force_reset=True,
                             tensorboard_log=None if args.no_tensorboard else str(run_dir / "tensorboard"))
            agent.seed = cfg["seed"]
            agent.set_random_seed(cfg["seed"])
        else:
            ppo = dict(cfg["ppo"])
            arch, log_std = ppo.pop("net_arch"), ppo.pop("log_std_init")
            agent = PPO("MlpPolicy", vec, device="cpu", verbose=1, seed=cfg["seed"],
                        tensorboard_log=None if args.no_tensorboard else str(run_dir / "tensorboard"),
                        policy_kwargs={"net_arch": {"pi": arch, "vf": arch}, "activation_fn": nn.Tanh,
                                       "log_std_init": log_std}, **ppo)
            if init_data:
                previous = PPO.load(str(init_data[0] / "model.zip"), device="cpu")
                agent.policy.load_state_dict(previous.policy.state_dict(), strict=True)
                del previous
        print(f"Task={cfg['task']} | A-model mass={RobotSpec.load(cfg).mass:.4f}kg | "
              f"{len(fns)} CPU envs | requested additional steps={cfg['train']['total_timesteps']}", flush=True)
        agent.learn(total_timesteps=cfg["train"]["total_timesteps"], callback=callback,
                    reset_num_timesteps=not bool(resume_data), tb_log_name=cfg["task"], progress_bar=False)
        metrics = evaluate_agent(agent, cfg, cfg["train"]["eval_episodes"], cfg["train"]["eval_seed"],
                                 command=cfg["train"]["eval_forward_m_s"])
        save_bundle(agent, run_dir / "final", cfg, interface, metrics)
        save_bundle(agent, run_dir / "latest", cfg, interface, metrics)
        if tuple(metrics["selection_key"]) > callback.best_key or not (run_dir / "best").exists():
            save_bundle(agent, run_dir / "best", cfg, interface, metrics)
        save_json(run_dir / "training_status.json", {"status": "TRAINING_FINISHED", "physics_executed": True,
                                                    "num_timesteps": int(agent.num_timesteps),
                                                    "evaluation": metrics,
                                                    "note": "Training completion is not proof of standing/walking success."})
        return 0
    except KeyboardInterrupt:
        if agent is not None:
            save_bundle(agent, run_dir / "interrupted", cfg, interface, callback.last_metrics)
        save_json(run_dir / "training_status.json", {"status": "INTERRUPTED", "checkpoint": "interrupted"})
        print("Interrupted checkpoint saved. Resume with --resume <run-dir>/interrupted.", flush=True)
        return 130
    except BaseException:
        (run_dir / "error.txt").write_text(traceback.format_exc(), encoding="utf-8")
        save_json(run_dir / "training_status.json", {"status": "ERROR", "see": "error.txt"})
        raise
    finally:
        callback.close()
        if vec is not None:
            vec.close()
