"""Reference phase boundaries must not teleport feet or COM."""
import unittest
from types import SimpleNamespace
import numpy as np

try:
    from probe_reference_gait import MovingCOMReference
except ImportError:
    MovingCOMReference = None


@unittest.skipIf(MovingCOMReference is None, "MuJoCo reference probe dependencies unavailable")
class ReferenceContinuityTests(unittest.TestCase):
    def planner(self):
        g = dict(step_length_m=.02, step_height_m=.004, initial_stand_s=1.,
                 shift_s=.14, swing_s=.22, settle_s=.04, com_inset_mm=20.)
        source = SimpleNamespace(initial_feet=np.array([[0.,.032,0.],[0.,-.032,0.]]),
                                 q0=np.zeros(10), b0=np.eye(4), seed=None, g=g, steps=4)
        def pose(feet, xy, seed, height):
            # A transparent pose sink exposes requested task-space continuity.
            q = np.r_[feet.ravel(), np.zeros(4)]
            base = np.eye(4); base[:2,3] = xy; base[2,3] = height
            return q, base, 0.
        def smooth(u):
            u = np.clip(u,0,1)
            return u**3*(10+u*(-15+6*u))
        return MovingCOMReference(source, pose, smooth, ("left","right"))

    def test_all_phase_boundaries_are_continuous(self):
        reference = self.planner()
        for step in range(4):
            for offset in (0., .14, .36, .4):
                t = 1.+step*.4+offset
                before, after = reference.sample(t-1e-8), reference.sample(t+1e-8)
                with self.subTest(time=t):
                    np.testing.assert_allclose(before.q, after.q, atol=1e-7, rtol=0)
                    np.testing.assert_allclose(before.base, after.base, atol=1e-7, rtol=0)
                    np.testing.assert_allclose(before.support, after.support, atol=1e-7, rtol=0)

    def test_both_feet_and_com_advance(self):
        end = self.planner().sample(3.)
        np.testing.assert_allclose(end.q[:6].reshape(2,3)[:,0], [.08,.06])
        np.testing.assert_allclose(end.base[:2,3], [.07,0.], atol=1e-12)
        np.testing.assert_allclose(end.support, [.5,.5])

    def test_com_offset_preserves_foot_and_support_trajectories(self):
        reference, shifted = self.planner(), self.planner()
        shifted.com_forward_offset_m = -.006
        for t in np.linspace(0, 3., 151):
            a, b = reference.sample(t), shifted.sample(t)
            np.testing.assert_allclose(a.q, b.q, atol=1e-12)
            np.testing.assert_allclose(a.support, b.support, atol=1e-12)
            np.testing.assert_allclose(b.base[:3,3]-a.base[:3,3], [-.006,0,0], atol=1e-12)
