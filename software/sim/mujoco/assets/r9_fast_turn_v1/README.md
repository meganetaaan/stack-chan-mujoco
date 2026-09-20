# r9 fast-turn model v1

Validated simulation candidate copied from development candidate v7 without changing model data. See [reproduction and results](../../docs/FAST_TURN_RUN_ja.md).

- Floating base, 12 actuated joints, unchanged actuator safety constraints.
- Preserved 128 mm body, Tab5 face, 50/44 mm leg lengths.
- Updated hip-yaw placement, 86×48 mm feet, battery tray, underside clearance.
- Both directions: six qualified footfalls; 90° ±1° stop, final landing confirmation, and body settling in approximately 2.76 seconds.

`DEVELOPMENT.json` records generation-time limitations. Subsequent measured evidence is stored separately in `validation/fast_turn_v1`. CAD strengths, fastener mass assumptions and physical actuator identification remain prototype limitations; this is not a hardware or manufacturing qualification.
