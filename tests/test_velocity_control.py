import unittest
import numpy as np
from velocity_control import keyboard_velocity,limit_velocity,VelocityControl


class VelocityTests(unittest.TestCase):
    def test_all_four_simultaneous_directions(self):
        for forward,key in [(1,'W'),(-1,'S')]:
            for turn,other in [(1,'A'),(-1,'D')]:
                v,w=keyboard_velocity({key,other})
                self.assertEqual(np.sign(v),forward)
                self.assertEqual(np.sign(w),turn)
        np.testing.assert_array_equal(keyboard_velocity({'W','S','A','D'}),[0,0])
        np.testing.assert_array_equal(keyboard_velocity({'W','A','SPACE'}),[0,0])
        self.assertEqual(keyboard_velocity({'W','S','A'})[0],0)
        self.assertGreater(keyboard_velocity({'W','S','A'})[1],0)

    def test_invalid_and_combined_limits(self):
        for bad in [[np.nan,0],[0,np.inf],[1,2,3]]:
            with self.assertRaises(ValueError):limit_velocity(bad)
        np.testing.assert_allclose(limit_velocity([1,10]),[.025,np.deg2rad(12)])
        np.testing.assert_allclose(limit_velocity([-1,-10]),[-.012,-np.deg2rad(12)])
        np.testing.assert_allclose(limit_velocity([0,10]),[0,np.deg2rad(32)])

    def test_feedback_slew_and_no_windup_after_stop(self):
        c=VelocityControl()
        for _ in range(250):
            c.observe([.0,0,0])
            old=c.target.copy();c.update([.02,.15])
            self.assertTrue(np.all(abs(c.target-old)<=np.array([.04,.8])*.02+1e-12))
        self.assertGreater(c.drive[0],c.target[0])
        self.assertGreater(c.drive[1],c.target[1])
        for _ in range(100):c.update([0,0])
        np.testing.assert_array_equal(c.drive,[0,0])
        np.testing.assert_array_equal(c.integral,[0,0])

    def test_feedback_observation_changes_drive(self):
        a,b=VelocityControl(),VelocityControl()
        for _ in range(150):
            a.observe([.01,0,.1]);b.observe([.03,0,.3])
            a.update([.02,.2]);b.update([.02,.2])
        self.assertTrue(np.all(a.drive>b.drive))

    def test_support_and_tilt_derate(self):
        c=VelocityControl()
        for _ in range(10):c.observe_support(0,[0,0])
        self.assertEqual(c.safety_scale,0)
        c.update([.01,.1]);np.testing.assert_array_equal(c.target,[0,0])
        c.observe_support(12,[1,0]);self.assertEqual(c.safety_scale,.5)
        c.observe_support(5,[1,0]);self.assertEqual(c.safety_scale,1)


if __name__=='__main__':unittest.main()
