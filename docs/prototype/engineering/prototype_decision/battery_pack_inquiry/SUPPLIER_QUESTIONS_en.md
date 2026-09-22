# Draft technical inquiry — protected 1S battery for a small robot

We are evaluating a manufacturer-assembled protected battery for twelve low-voltage robot actuators. We are considering P2150R or P1831R with factory-fitted leads and a connector. This is a technical inquiry draft, not a purchase order.

Our current engineering comparison budget is 9.834 A total. This is not yet a verified hardware current limit or a measured worst-case peak. The actuators require 3.7–6.0 V at their terminals, so voltage drop and usable discharge capacity are particularly important. The battery would be removed from the robot for charging; a separate supply is planned for its display computer.

Your standard wired versions list a JST SYP-02 connector. JST specifies 3 A with AWG22 for the RCY series. Please clarify the continuous rating of the complete wired assembly and whether a factory-assembled version with a suitable higher-current connection is available.

Please provide, or explicitly mark as unavailable:

1. Exact orderable part number and revision; internal cell and protection configuration; confirmation that the supplied external terminals are both on the protected side.
2. Complete assembly continuous and pulse current ratings, temperature conditions, duty cycle and any derating. Include the limiting ratings of the protection circuit, internal joints, leads and connector.
3. Lead gauge/material, length, insulation, termination and strain relief; connector manufacturer, exact mating part numbers, polarity drawing, and maximum loop resistance of the external lead/connector assembly with its test conditions.
4. Maximum dimensions including leads and strain relief, minimum/maximum body dimensions, complete mass, and recommended mounting/retention precautions.
5. Overcharge, overdischarge, overcurrent, short-circuit and temperature protection thresholds, tolerances, detection delays, recovery behavior and initial activation procedure.
6. Loaded discharge voltage/capacity data relevant to approximately 1 A, 5 A and 10 A, including test temperature and age/condition. Please distinguish typical curves from guaranteed limits. We need to determine usable energy above the robot's voltage cutoff, rather than capacity down to 2.5 V.
7. Whether reverse charging current from motor regeneration is permitted, including current/time limits near full charge and at temperature limits; behavior when charging protection opens. A standard CC-CV charge-current rating alone does not resolve this question.
8. Recommended compatible external charger and its voltage/current limits, termination and protection-recovery procedure.

We will separately design robot undervoltage shutdown, branch protection, motor-side transient control and manual restart. We do not assume the battery protection alone provides these functions. If no suitable wired version is available, please state that rather than substituting the standard 3 A connector assembly.
