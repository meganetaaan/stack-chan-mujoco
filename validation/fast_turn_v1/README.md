# r9 fast-turn verification

The exact tested model is published in `assets/r9_fast_turn_v1`. See [Japanese reproduction guide](../../docs/FAST_TURN_RUN_ja.md).

- `trials/`: two nominal and eight one-factor sensitivity trials, including all states, 1 ms contact traces, assessments, source-freeze plan and logs. All ten passed. No trials were replaced.
- `left_cad_audit.json`, `right_cad_audit.json`: 45 CAD parts, 63 recorded poses per direction; no cross-link intersection above 0.01 mm³. Corresponding body transforms are included. This is discrete sampled evidence, not a continuous clearance proof.
- `physics_invariants.json`: preserved actuator bounds and physics settings; no added equality constraints or contact exclusions; no home-pose penetration in the 961-pose yaw grid.
- `left_turn.mp4`: replay of the recorded nominal left-turn states, at 50 fps. The robot trajectory is not synthesized.
- `prior_acceptance_recheck.json`: the previous r8 result remains fixed 20/20 and randomized 18/20; those results are not attributed to r9.
- `completion_audit.json`: independent quaternion-derived turn assessment and replay of the 1 ms landing qualification. All ten trials complete the stable stop and six-footfall confirmation in 2.515–2.532 seconds.
- `completion_audit_full_settle.json`: additionally requires body translation <=0.02 m/s and total angular speed <=10 deg/s through the remaining trial (at least one second). All ten fully settle at 2.76 seconds. This stricter result is used for the final completion claim.
- `rebuild_check.json`: the published scene, inertias, joint map and robot parameters are byte-identical to a fresh model rebuild.

Development paths in provenance records identify the original execution locations. Archived files and the published model retain the same data. Earlier candidates and unsuccessful trials remain in `validation/fast_turn_development_v1`.

All results are MuJoCo results. The sensitivity suite varies one factor at a time; it does not establish hardware reliability or success over arbitrary combined disturbances.
