# R7 hip-yaw dynamics candidate — development only

This is a separate 12-axis floating-base model, not a validated walking robot or a manufacturing release. The support/horn geometry and shaft-to-case placement remain provisional. Material density and uniform actuator envelopes are assumptions inherited from the earlier CAD model; stiffness and hardware parameters are not identified.

See `validation/yaw_dynamics_development_v1/README.md` for the failed dynamics probes, exact limitations and regeneration commands. CAD parts and CAD-derived inertias are included. The original R6 mounted-battery model remains unchanged.

## Actuator comparison variant

Both ankle-pitch motors use the XC330 specification, including mass, inertia, speed and torque limits. See `ANKLE_UPGRADE.json` for provenance. The simulation torque cap is not a manufacturer continuous rating.

Knee case rotation about the existing output axes: 0 degrees. Joint axes and leg lengths are unchanged. Rotated cases are packaging experiments, not validated mounting designs. No walking acceptance is claimed.
