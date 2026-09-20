import unittest
import numpy as np
from crab_control import crab_keyboard,LateralControl
from velocity_control import keyboard_velocity
from teleop_yaw import ROOT,Simulation


class CrabTests(unittest.TestCase):
    def test_shift_keys_translate_without_requested_yaw(self):
        for key,expected in [('W',[.015,0,0]),('S',[-.008,0,0]),('A',[0,.004,0]),('D',[0,-.004,0])]:
            np.testing.assert_allclose(crab_keyboard({key}),expected)
        np.testing.assert_allclose(crab_keyboard({'W','A'}),[.015,.004,0])
        np.testing.assert_array_equal(crab_keyboard({'W','S','A','D'}),[0,0,0])
        np.testing.assert_array_equal(crab_keyboard({'W','A','SPACE'}),[0,0,0])
        self.assertGreater(keyboard_velocity({'A'})[1],0)

    def test_side_limits_and_stop(self):
        c=LateralControl()
        for _ in range(100):
            previous=c.target;c.update(1,0,True)
            self.assertLessEqual(abs(c.target-previous),.0002+1e-12)
            self.assertLessEqual(c.drive,.006)
        self.assertEqual(c.target,.004)
        for _ in range(50):c.update(0,0,True)
        self.assertEqual(c.drive,0);self.assertEqual(c.integral,0)
        with self.assertRaises(ValueError):c.update(float('nan'),0,True)

    def test_lateral_step_is_latched_while_airborne(self):
        sim=Simulation(ROOT/'assets/r9_fast_turn_v1/reference',ROOT/'assets/r9_fast_turn_v1',fast_turn=True)
        r=sim.reference;r.set_command((0,.004,0),0);r.sample(0)
        self.assertEqual(r.stance,1)
        self.assertGreater(r.lateral_target,r.feet[r.swing,1])
        r.sample(.24);end=r.end;target=r.lateral_target
        r.set_command((0,-.004,0),.24);r.sample(.24)
        self.assertEqual(r.end,end);self.assertEqual(r.lateral_target,target)


if __name__=='__main__':unittest.main()
