"""v4 credit assigned from consecutive *actual* confirmed landing events.

No modification of measured counts, clearance, minimum airtime or success
thresholds. A repeated landing updates the predecessor even if it earns no
reward. A cooldown-ineligible opposite foot also updates it. Thus suppressed
credits cannot create fake alternation. Simultaneous landings are ambiguous:
no credit, no invented left-before-right ordering for reward purposes.
"""
from __future__ import annotations


class OrderedStepCredit:
    def __init__(self, cooldown_s: float):
        self.cooldown = float(cooldown_s)
        self.last = None
        self.last_credit_s = -float("inf")
        self.was_active = False
        self.totals = {"ordered_rewarded_landings": 0,
                       "ordered_forward_landings": 0,
                       "ordered_alternating_landings": 0,
                       "ordered_repeated_landings": 0,
                       "simultaneous_landing_frames": 0}

    def update(self, events: dict, time_s: float, active: bool) -> dict:
        out = {"ordered_rewarded_landings_this_step": 0,
               "ordered_forward_landings_this_step": 0,
               "ordered_alternating_landings_this_step": 0,
               "ordered_repeated_landings_this_step": 0,
               "simultaneous_landing_frames_this_step": 0}
        if not active:
            self.last, self.was_active = None, False
            self.last_credit_s = -float("inf")
            return out
        if not self.was_active:
            self.last = None
            self.last_credit_s = -float("inf")
        self.was_active = True
        feet = list(events.get("valid_landing_feet", []))
        if len(feet) > 1:
            out["simultaneous_landing_frames_this_step"] = 1
            self.last = None
            self.last_credit_s = time_s
        elif feet:
            foot = int(feet[0])
            repeated = self.last == foot
            out["ordered_repeated_landings_this_step"] = int(repeated)
            eligible = not repeated and time_s-self.last_credit_s+1e-10 >= self.cooldown
            forward = foot in events.get("forward_landing_feet", [])
            if eligible:
                out["ordered_rewarded_landings_this_step"] = 1
                out["ordered_forward_landings_this_step"] = int(forward)
                out["ordered_alternating_landings_this_step"] = int(self.last is not None and forward)
                self.last_credit_s = time_s
            self.last = foot
        for key in self.totals:
            self.totals[key] += out[key+"_this_step"]
        return out
