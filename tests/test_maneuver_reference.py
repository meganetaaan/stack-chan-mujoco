import json
from pathlib import Path
from types import SimpleNamespace
import unittest
import numpy as np
from maneuver_reference import CommandReference


class CommandReferenceTests(unittest.TestCase):
    def planner(self):
        initial = SimpleNamespace(initial_feet=np.array([[0., .022, 0.], [0., -.022, 0.]]),
                                  q0=np.zeros(10), b0=np.eye(4))
        def pose(feet, xy, seed, height):
            return seed[0], seed[1], 0.
        def smooth(t):
            x = np.clip(t, 0, 1)
            return x**3*(10+x*(-15+6*x))
        protocol = json.loads(Path('configs/maneuver/acceptance_v1.json').read_text())
        return CommandReference(initial, pose, smooth, protocol)

    def test_boundary_geometry_has_no_teleport_and_stop_aligns_feet(self):
        planner = self.planner()
        geometry = []
        for t in np.arange(0, 32.001, .02):
            planner.sample(t)
            feet, xy, support, _ = planner.geometry(t)
            geometry.append(np.r_[feet.ravel(), xy])
            if 16<=t<18 or 30<=t<32:
                self.assertEqual(planner.mode, 'stand')
                self.assertAlmostEqual(feet[0, 0], feet[1, 0])
                np.testing.assert_allclose(support, [.5, .5], atol=1e-12)
        # Bound Cartesian changes between neighboring 20 ms samples. A reset
        # to nominal feet at the forward/backward boundary would fail this.
        self.assertLess(np.max(abs(np.diff(geometry, axis=0))), .02)
        self.assertLess(geometry[1400][0], geometry[900][0])

    def test_yaw_command_does_not_fabricate_root_rotation(self):
        planner = self.planner()
        for t in np.arange(0, 42.001, .02):
            sample = planner.sample(t)
        np.testing.assert_array_equal(sample.base[:3, :3], np.eye(3))
        with self.assertRaises(ValueError):
            planner.sample(0.)


if __name__ == '__main__':
    unittest.main()
