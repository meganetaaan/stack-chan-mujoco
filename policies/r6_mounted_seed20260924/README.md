# Mounted-battery PPO candidate

Parent: `policies/r6_steering_seed20260923`. Initial weights are transferred from that trained policy; fresh optimizer, 32,768 additional PPO steps on `assets/r6_mounted_battery`, seed 20260924. This is a new plant with tray/strap/fastener mass and collisions. No acceptance result is claimed until the predeclared 40 trials complete.

Reproduce with `train_mounted_residual.py`; evaluate with `run_planned_r6_evaluation.py --checkpoint policies/r6_mounted_seed20260924 --seed-plan configs/r6/mounted_evaluation_seeds.json --out outputs/r6_mounted_acceptance`. Full instructions: `docs/R6_RL_ja.md`. Hardware not tested.
