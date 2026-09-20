# Yaw shaft offset and drilled flange candidate

Development only; not a manufacturing release or maneuver acceptance result.

The joint axes and old leg/foot geometry remain unchanged. The yaw case long
axis now runs along robot X, with its center 7.5 mm behind the output shaft.
A 34 x 20 x 23 mm case envelope and a separate rotating 16 mm diameter,
3 mm horn envelope replace the centered 20 x 34 x 26 mm box. Rear idler is
not installed in this variant. See design/x330_manufacturer_reference.json.

The rotating printed coupler has a 16 mm diameter, 2 mm flange, with four
2.2 mm clearance holes on a 12 mm pitch circle. These are proposed clearance
holes, not the manufacturer's 1.6 mm tapping holes. Actual screw length,
head clearance, access, fixed-case mounting and strength remain unresolved.
The battery tray webs are rerouted for 0.8 mm nominal radial flange clearance.

Total mass: 0.9354361441264678 kg. Motor mass remains 18 g each, distributed
between the case and horn in proportion to proxy volume. This uniform-density
approximation is explicit; the vendor inertia tensor has NOT been applied.
The generic cable/fastener allowance is retained; no exact new screw BOM exists.

The discrete home-pose yaw sweep has no yaw-mount penetration, but opposing
extreme yaw angles collide between the legs/feet in 6 of 361 sampled poses.
Consequently the Cartesian product of joint limits is not a safe pose set.
No collision exemptions or relaxed evaluation thresholds were introduced.

Rebuild with build_yaw_dynamics_candidate.py --manufacturer-yaw-layout, then
upgrade_candidate_ankles.py. Full command lines and development results are
in validation/yaw_offset_flange_development_v1/README.md.
