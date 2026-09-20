"""Contact-based footstep counting, independent of MuJoCo and of reward."""
from __future__ import annotations
import numpy as np


class FootStepTracker:
    def __init__(self, dt: float, minimum_airtime: float, minimum_lift: float):
        self.dt, self.minimum_airtime, self.minimum_lift = dt, minimum_airtime, minimum_lift
        self.airtime = np.zeros(2)
        self.supported_airtime = np.zeros(2)
        self.peak = np.zeros(2)
        self.touched = np.zeros(2, dtype=bool)
        self.counts = np.zeros(2, dtype=int)
        self.sequence: list[str] = []

    def update(self, contacts, heights) -> int:
        contacts = np.asarray(contacts, dtype=bool)
        heights = np.asarray(heights, dtype=float)
        events = 0
        for i in range(2):
            if contacts[i]:
                if (self.touched[i] and self.airtime[i] + 1e-10 >= self.minimum_airtime
                    and self.peak[i] >= self.minimum_lift
                    and self.supported_airtime[i] >= 0.5*self.airtime[i]):
                    self.counts[i] += 1
                    self.sequence.append("left" if i == 0 else "right")
                    events += 1
                self.touched[i] = True
                self.airtime[i] = self.supported_airtime[i] = self.peak[i] = 0.0
            elif self.touched[i]:
                self.airtime[i] += self.dt
                self.supported_airtime[i] += self.dt*float(contacts[1-i])
                self.peak[i] = max(self.peak[i], heights[i])
        return events
