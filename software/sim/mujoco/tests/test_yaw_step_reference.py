import unittest
import numpy as np
from generate_yaw_step_reference import foot_yaw


class FootYawCycleTests(unittest.TestCase):
    def test_stance_rate_and_swing_boundary_continuity(self):
        period=.32;rate=np.pi/20;epsilon=1e-7
        for leg in (0,1):
            start=1.+(.35+(leg==0))*period
            for cycle in range(4):
                for boundary in (start+cycle*2*period,start+cycle*2*period+.55*period):
                    left=foot_yaw(boundary-epsilon,leg,rate,period)
                    at=foot_yaw(boundary,leg,rate,period)
                    right=foot_yaw(boundary+epsilon,leg,rate,period)
                    self.assertAlmostEqual((at-left)/epsilon,-rate,places=5)
                    self.assertAlmostEqual((right-at)/epsilon,-rate,places=5)
            values=np.array([foot_yaw(t,leg,rate,period) for t in np.arange(0,12,.001)])
            self.assertLess(np.max(abs(values)),.075)

    def test_zero_and_direction_symmetry(self):
        for t in np.arange(0,5,.017):
            for leg in (0,1):
                self.assertEqual(foot_yaw(t,leg,0,.32),0.)
                self.assertEqual(foot_yaw(t,leg,.1,.32),-foot_yaw(t,leg,-.1,.32))


if __name__=='__main__':unittest.main()
