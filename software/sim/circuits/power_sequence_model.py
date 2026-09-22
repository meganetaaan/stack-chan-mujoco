"""Sampled contract for dual-rail sequencing, not a GPIO or analog timing model.

Inputs are independent observations. This module never clears the external latch
or generates its own acknowledgement. A future hardware implementation must
qualify each input, implement deadlines and preserve asynchronous inhibition.
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class Inputs:
    independent_health: bool
    left_source: bool
    right_source: bool
    left_pg: bool
    right_pg: bool
    armed: bool
    permission: bool
    clr_low: bool
    hold_done: bool
    startup_expired: bool

    @property
    def healthy(self):
        return self.independent_health and self.left_source and self.right_source

@dataclass(frozen=True)
class State:
    phase: str = 'CLEAR'
    clear_phase: str = 'RESET_TIMER'
    permission_low_seen: bool = False

@dataclass(frozen=True)
class Outputs:
    enable_request: bool
    clear_request: bool
    reset_low_valid: bool
    startup_timer_run: bool


def outputs(s, i):
    fault = (not i.healthy or not i.permission or not i.armed or i.clr_low or
             (s.phase == 'RUN' and not (i.left_pg and i.right_pg)) or
             (s.phase == 'START' and i.startup_expired))
    return Outputs(
        enable_request=s.phase in ('START', 'RUN') and not fault,
        clear_request=s.phase == 'CLEAR',
        reset_low_valid=s.phase == 'CLEAR' and s.clear_phase == 'QUALIFY'
                        and i.healthy and i.clr_low,
        startup_timer_run=s.phase == 'START',
    )


def advance(s, i):
    if s.phase == 'CLEAR':
        if not i.healthy or not i.clr_low:
            return State()
        if s.clear_phase == 'RESET_TIMER':
            return State('CLEAR', 'QUALIFY' if not i.hold_done else 'RESET_TIMER')
        if s.clear_phase != 'QUALIFY':
            return State()
        if i.hold_done and not i.armed and not i.permission:
            # Must subsequently observe permission Low outside asserted clear.
            return State('WAIT_NEW_PRESS')
        return s
    if s.phase == 'WAIT_NEW_PRESS':
        if not i.healthy:
            return State()
        if not i.permission:
            return State('WAIT_NEW_PRESS', permission_low_seen=not i.clr_low)
        if not i.armed or i.clr_low:
            return State()  # Inconsistent permission must be cleared, not remembered.
        if s.permission_low_seen:
            # Refuse a stale expired timer before launching a fresh START.
            return State() if i.startup_expired else State('START')
        return s
    if s.phase in ('START', 'RUN'):
        if not i.healthy or not i.permission or not i.armed or i.clr_low:
            return State()
        if s.phase == 'START':
            # Timeout wins a simultaneous PG rise, rather than masking a timeout.
            if i.startup_expired:
                return State()
            return State('RUN') if i.left_pg and i.right_pg else s
        return s if i.left_pg and i.right_pg else State()
    return State()  # Invalid state inhibits and requests a fresh clear.
