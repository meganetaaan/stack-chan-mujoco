# Revised boot versus manufacturer servo CAD

Both boots were checked against all 15 solids of the manufacturer X330 STEP, at 11 ankle-roll angles per side (330 pair evaluations). The minimum sampled clearance is 8.005623024 mm on each side. No sampled overlap or clearance below the predeclared 1.1 mm criterion was found.

Case parts are fixed. Horns, idler, cap and central screws (indices 3,9,10,11,12) are assumed to co-rotate. This explicit hypothesis requires assembly qualification. Manufacturer screw names do not approve purchase lengths. New horn mounting screws, harness and deformation are absent. The result is discrete, not a continuous sweep certificate or Issue #19 completion. Full robot trajectories, other parts, actual tolerance and deflection remain open.

## Reproduce

```sh
export LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu"
.venv-engineering/bin/python software/sim/structural/check_boot_native_servo.py --out outputs/reproduce_boot_servo
```

Use a new output directory. plan.json records input hashes and criteria before evaluation; report.json contains all pair distances and nearest points. No manufacturing release is approved.
