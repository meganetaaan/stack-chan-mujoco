"""Explicit transfer instead of inheriting a collapsed exploration distribution."""
from __future__ import annotations


def transfer_policy(source, destination, *, actor_only: bool, reset_log_std: float | None) -> dict:
    """Compatible SB3 MlpPolicy architectures only; optimizer remains NEW.

    Actor-only copies policy feature/MLP and action head weights, not value-net
    weights. Parameter names must match; shared *trainable* feature extractors
    are refused in actor-only mode (this kit uses parameter-free Flatten).
    """
    import torch
    src, dst = source.state_dict(), destination.state_dict()
    if set(src) != set(dst) or any(src[k].shape != dst[k].shape for k in src):
        raise ValueError("Policy architectures do not match; cannot transfer safely")
    if actor_only:
        if any(k.startswith("features_extractor.") for k in src):
            raise ValueError("Actor-only transfer requires the kit's parameter-free Flatten extractor")
        keys = [k for k in src if k.startswith(("mlp_extractor.policy_net.", "action_net.", "pi_features_extractor."))]
        if not any(k.startswith("action_net.") for k in keys):
            raise ValueError("No recognized SB3 actor weights found")
        state = dict(dst)
        for k in keys:
            state[k] = src[k]
        # Unless explicitly reset, retain the old actor's exploration.
        state["log_std"] = src["log_std"]
    else:
        keys = list(src)
        state = src
    destination.load_state_dict(state, strict=True)
    old_std = source.log_std.detach().cpu().tolist()
    if reset_log_std is not None:
        with torch.no_grad():
            destination.log_std.fill_(float(reset_log_std))
    return {"copied_actor_only": bool(actor_only), "copied_tensor_count": len(keys),
            "critic": "new initialization" if actor_only else "copied",
            "optimizer": "new", "source_log_std": old_std,
            "destination_log_std": destination.log_std.detach().cpu().tolist()}
