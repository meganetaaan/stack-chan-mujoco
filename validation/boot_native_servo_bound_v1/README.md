# Continuous bound from boot / servo samples

The prior 330 CAD pair evaluations are extended to continuous ankle roll over −0.34 to +0.34 rad. Input CAD hashes are rechecked and every side/component must have exactly the declared angle samples. Thirty component pairs and their ten intervals each are retained in report.json. The minimum interval lower bound is **2.289530449 mm**, exceeding the unchanged **1.1 mm** clearance criterion.

For a stationary servo component, every angle in an interval is at most half the interval width from a sampled endpoint. Every point in the boot moves by at most R times that angle difference, where R bounds the radial distance from the X axis using the CAD bounding box. Hence min(endpoint distances) − R·width/2 is a conservative lower bound. A further 0.00001 mm numerical allowance is subtracted. For components co-rotating rigidly with the boot, distance is invariant, so only the numerical allowance is subtracted.

This is conditional on the motion groups in the input plan (indices 3,9,10,11,12 rotate), rigid geometry, and assumed CAD numerical allowance. Cap/screw motion and actual attachment are not qualified by this calculation. New mounting screws, cables, full leg trajectories, actual tolerances and elastic deflection are not evaluated. Neither Issue #19 nor manufacturing release is complete.

## Reproduce

```sh
export LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu"
.venv-engineering/bin/python software/sim/structural/bound_boot_servo_samples.py --out outputs/reproduce_boot_servo_bound
```

Use a new output directory. Prior samples remain in validation/boot_native_servo_development_v1. The frozen input checker and CAD hashes must match or evaluation stops.
