"""Tab5 restart contract. Inputs require external qualification, not raw GPIO.

No analog power-off detector, timer implementation or servo latch is supplied.
The output is one necessary permission input to the existing dual-rail sequencer.
"""
from dataclasses import dataclass

MIN_OFF_MS = 5000

@dataclass(frozen=True)
class Inputs:
    healthy: bool = True  # Includes main supply established, no precharge/fault.
    off_verified: bool = False
    continuous_observation: bool = True  # False after missed/unknown observations.
    power_valid: bool = False
    ready: bool = False  # Fresh readiness for this boot, not retained old ready.
    request: bool = False  # New explicit power-start request.
    arm: bool = False  # New explicit drive request, after readiness.
    stop: bool = False
    shutdown_ack: bool = False  # Fresh acknowledgement for current shutdown.

@dataclass(frozen=True)
class State:
    phase: str = 'OFF'
    off_since: int | None = None
    previous_ms: int | None = None
    request_low_seen: bool = False
    arm_low_seen: bool = False

@dataclass(frozen=True)
class Outputs:
    tab5_allow: bool
    drive_permission: bool
    shutdown_request: bool


def outputs(s, i):
    valid = i.healthy and i.continuous_observation
    enabled = valid and s.phase in ('BOOT', 'READY', 'RUN', 'SHUTDOWN')
    if s.phase in ('READY', 'RUN') and not (i.power_valid and i.ready):
        enabled = False
    if s.phase == 'SHUTDOWN' and (i.shutdown_ack or not i.power_valid):
        enabled = False
    return Outputs(enabled,
                   valid and s.phase == 'RUN' and i.power_valid and i.ready and not i.stop,
                   valid and s.phase == 'SHUTDOWN' and not i.shutdown_ack)


def advance(s, i, now_ms):
    # A reset uses State(), discarding elapsed time and remembered permissions.
    if (not isinstance(now_ms, int) or isinstance(now_ms, bool) or now_ms < 0
            or (s.previous_ms is not None and now_ms < s.previous_ms)):
        return State()
    if not i.healthy or not i.continuous_observation:
        return State(previous_ms=now_ms)
    if s.phase == 'OFF':
        since = s.off_since if i.off_verified else None
        if i.off_verified and since is None:
            since = now_ms
        low = s.request_low_seen or not i.request
        elapsed = since is not None and now_ms - since >= MIN_OFF_MS
        # A high request presented too early is consumed, never deferred.
        rising = s.request_low_seen and i.request
        if i.request:
            low = False
        if elapsed and rising and not i.stop:
            return State('BOOT', previous_ms=now_ms)
        return State('OFF', since, now_ms, low)
    if s.phase == 'BOOT':
        if i.stop:
            return State('SHUTDOWN', previous_ms=now_ms)
        if i.power_valid and i.ready:
            return State('READY', previous_ms=now_ms)
        return State('BOOT', previous_ms=now_ms)
    if s.phase in ('READY', 'RUN'):
        if not i.power_valid or not i.ready:
            return State(previous_ms=now_ms)
        if i.stop:
            return State('SHUTDOWN', previous_ms=now_ms)
        if s.phase == 'RUN':
            return State('RUN', previous_ms=now_ms)
        if s.arm_low_seen and i.arm:
            return State('RUN', previous_ms=now_ms)
        return State('READY', previous_ms=now_ms, arm_low_seen=not i.arm)
    if s.phase == 'SHUTDOWN':
        if i.shutdown_ack or not i.power_valid:
            return State(previous_ms=now_ms)
        return State('SHUTDOWN', previous_ms=now_ms)
    return State(previous_ms=now_ms)
