"""50 Hz target telemetry, separate from raw action and physical joint motion."""
from __future__ import annotations
import numpy as np


class TargetMotionMetrics:
    def __init__(self, initial_target, measurement_start_s: float):
        self.previous = np.asarray(initial_target, dtype=float).copy()
        self.start_s = float(measurement_start_s)
        self.count = 0
        self.sum_sq = np.zeros(10)
        self.last_delta = np.zeros(10)

    def observe(self, target, time_s: float) -> None:
        target = np.asarray(target, dtype=float)
        if target.shape != (10,) or not np.isfinite(target).all():
            raise ValueError("Expected ten finite post-filter targets")
        self.last_delta = target-self.previous
        self.previous = target.copy()
        if time_s+1e-10 >= self.start_s:
            self.sum_sq += self.last_delta**2
            self.count += 1

    def summary(self) -> dict:
        rms = np.sqrt(self.sum_sq/max(1, self.count))
        return {"target_metric_samples": self.count,
                "target_delta_rms_rad_each": rms.tolist(),
                # Same arithmetic mean across per-joint RMS as the 40ms probe.
                "target_delta_rms_rad_mean": float(rms.mean()),
                "target_delta_global_rms_rad": float(np.sqrt(np.mean(self.sum_sq/max(1, self.count))))}
