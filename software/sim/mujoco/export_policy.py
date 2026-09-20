#!/usr/bin/env python3
"""Export deterministic MLP actor as TorchScript + its exact I/O contract.
The output still requires the simulator observation builder and servo controller.
"""
from __future__ import annotations
import argparse
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--checkpoint", type=Path, required=True)
    p.add_argument("--out", type=Path, default=Path("outputs/exported_policy"))
    args = p.parse_args()
    import torch
    from torch import nn
    from stable_baselines3 import PPO
    from stackchan_rl.checkpoints import bundle_info, assert_interface
    from stackchan_rl.config import save_json
    from stackchan_rl.spec import OBS_DIM
    folder, cfg, interface, _ = bundle_info(args.checkpoint)
    assert_interface(interface, cfg)
    model = PPO.load(str(folder / "model.zip"), device="cpu")
    model.policy.set_training_mode(False)
    if model.use_sde or model.policy.squash_output:
        raise ValueError("This exporter supports the supplied unsquashed Gaussian MLP policy only")

    class Actor(nn.Module):
        def __init__(self, policy):
            super().__init__()
            self.features = policy.pi_features_extractor
            self.mlp = policy.mlp_extractor.policy_net
            self.action = policy.action_net

        def forward(self, observation):
            return self.action(self.mlp(self.features(observation))).clamp(-1.0, 1.0)

    actor = Actor(model.policy).eval()
    sample = torch.zeros(1, OBS_DIM, dtype=torch.float32)
    traced = torch.jit.trace(actor, sample)
    check = torch.randn(8, OBS_DIM).clamp(-cfg["env"]["obs_clip"], cfg["env"]["obs_clip"])
    with torch.no_grad():
        reference = model.predict(check.numpy(), deterministic=True)[0]
        actual = traced(check).numpy()
    import numpy as np
    if not np.allclose(actual, reference, atol=1e-6):
        raise RuntimeError("Exported actor differs from SB3 deterministic prediction")
    args.out.mkdir(parents=True, exist_ok=True)
    traced.save(str(args.out / "actor.ts"))
    save_json(args.out / "interface.json", interface)
    save_json(args.out / "config.json", cfg)
    save_json(args.out / "export_check.json", {"max_absolute_error": float(np.max(abs(actual-reference))),
                                              "hardware_ready": False})
    print(args.out.resolve())

if __name__ == "__main__":
    main()
