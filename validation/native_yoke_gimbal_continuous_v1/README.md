# Native ankle yoke / gimbal continuous clearance bound

The wider lower-bridge relief candidate and native-horn yoke were checked over ankle roll −0.34 to +0.34 rad on both sides. Each side required 33 distance samples and 16 accepted intervals. The minimum interval lower bound is **1.1272296095 mm**, above the predeclared **1.1 mm** nominal requirement.

For a point at radius at most R from the roll axis, rotation by δ changes its position by at most R|δ|. Set-to-set distance is Lipschitz under this displacement. Therefore the midpoint distance minus R times the half-interval is a lower bound throughout the interval. R is conservatively obtained from the moving CAD bounding box. The checker also subtracts 0.00001 mm as a numerical allowance and verifies that accepted intervals cover the full 0.68 rad range. This is conditional on the CAD kernel and numerical allowance, not a formal interval-arithmetic certificate.

The 1.1 mm allocation comprises 0.5 mm residual clearance, 0.4 mm combined surface tolerances, and 0.2 mm relative deflection. Actual manufacturing tolerances and structural deflection have not been qualified. The result covers only this pair of rigid parts. Boot clearance, motor mounting, fasteners, harness, full robot trajectories and strength remain open. No joint limit expansion or manufacturing release is approved.

## Reproduce

From repository root, with the engineering environment installed:

```sh
export LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu"
.venv-engineering/bin/python software/sim/structural/certify_native_yoke_gimbal.py --gimbal-dir validation/native_yoke_gimbal_wider_relief_v1/cad --out outputs/reproduce_native_continuous
```

Use a new output directory. Input hashes, criterion and limits are written before the evaluation in plan.json. report.json retains all samples and interval bounds. The exact checker is archived alongside the results.
