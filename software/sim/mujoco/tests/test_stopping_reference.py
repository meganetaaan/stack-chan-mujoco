"""Final-foot alignment must preserve the preceding gait and phase continuity."""
import unittest
import numpy as np
from tests import test_reference_gait as fixtures
from stopping_reference import AlignedStopReference


class StoppingReferenceTests(unittest.TestCase):
    def make(self):
        base = fixtures.ReferenceContinuityTests().planner()
        stop = AlignedStopReference(base,base.pose,base.smooth,base.sides,finish_shift_s=.3)
        return base,stop

    def test_preceding_steps_unchanged(self):
        base,stop = self.make()
        for t in np.linspace(0,2.19,100):
            a,b = base.sample(t),stop.sample(t)
            np.testing.assert_allclose(a.q,b.q,atol=1e-12)
            np.testing.assert_allclose(a.base,b.base,atol=1e-12)
            np.testing.assert_allclose(a.support,b.support,atol=1e-12)

    def test_final_phase_boundaries_are_continuous(self):
        _,stop = self.make()
        for t in (2.2,2.34,2.56,2.6,2.9):
            a,b = stop.sample(t-1e-8),stop.sample(t+1e-8)
            np.testing.assert_allclose(a.q,b.q,atol=1e-7,rtol=0)
            np.testing.assert_allclose(a.base,b.base,atol=1e-7,rtol=0)
            np.testing.assert_allclose(a.support,b.support,atol=1e-7,rtol=0)

    def test_finishes_with_aligned_feet_and_double_support(self):
        _,stop = self.make()
        end = stop.sample(3.)
        np.testing.assert_allclose(end.q[:6].reshape(2,3)[:,0],[.06,.06])
        np.testing.assert_allclose(end.support,[.5,.5])
        np.testing.assert_allclose(end.base[:2,3],[.06,0],atol=1e-12)


if __name__ == '__main__':
    unittest.main()
