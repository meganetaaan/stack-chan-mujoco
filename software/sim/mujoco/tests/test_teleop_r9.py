"""Physical smoke regressions for the interactive r9 adapter, not acceptance trials."""
import unittest
import numpy as np
from teleop_yaw import Simulation, ROOT


def r9():
    model = ROOT/'assets/r9_fast_turn_v1'
    return Simulation(model/'reference', model, fast_turn=True)


class R9TeleopTests(unittest.TestCase):
    def run_segment(self, sim, command, seconds):
        for _ in range(round(seconds/.02)):
            sim.step(command)
            self.assertIsNone(sim.failure, (command, sim.d.time, sim.failure))

    def test_model_reference_isolation_and_reset(self):
        new = r9()
        old = Simulation(ROOT/'design/teleop_reference', ROOT/'assets/r8_yaw_offset_flange_v1')
        reset = r9()
        self.assertEqual(new.legacy.KIN['hip_half_spacing_mm'], 26)
        self.assertEqual(old.legacy.KIN['hip_half_spacing_mm'], 22)
        self.assertIsNot(new.legacy.INERTIALS, reset.legacy.INERTIALS)
        np.testing.assert_array_equal(new.d.qpos, reset.d.qpos)

    def test_reversal_keeps_current_airborne_step(self):
        ref = r9().reference
        ref.set_command('right', 0.)
        ref.sample(0.)
        self.assertEqual(ref.stance, 1)
        ref.sample(.24)
        end = ref.end
        q = ref.sample(.24).q12
        ref.set_command('left', .24)
        # Repeated COM/IK solves refine the seed below microradian scale.
        np.testing.assert_allclose(q, ref.sample(.24).q12, rtol=0, atol=1e-6)
        self.assertEqual(ref.end, end)

    def test_continuous_turns_both_signs_and_release(self):
        for command, sign in [('left', 1), ('right', -1)]:
            with self.subTest(command=command):
                sim = r9()
                self.run_segment(sim, 'stop', 2.)
                headings = []
                for _ in range(300):
                    self.run_segment(sim, command, .02)
                    w,x,y,z = sim.d.qpos[3:7]
                    headings.append(np.arctan2(2*(w*z+x*y),1-2*(y*y+z*z)))
                self.assertGreater(sign*np.rad2deg(np.unwrap(headings)[-1]), 200.)
                self.run_segment(sim, 'stop', 3.)
                self.assertEqual(sim.reference.mode, 'stand')
                self.assertLess(np.linalg.norm(sim.d.qvel[:3]), .02)
                self.assertLess(np.linalg.norm(sim.d.qvel[3:6]), np.deg2rad(10))

    def test_all_directed_command_transitions(self):
        commands = ['stop', 'forward', 'backward', 'left', 'right']
        # Euler circuit visits all 20 directed transitions; boundaries are off
        # the 0.4 s gait grid to exercise requests made with an airborne foot.
        edges = {a:[b for b in commands if b != a] for a in commands}
        stack, route = ['stop'], []
        while stack:
            if edges[stack[-1]]:stack.append(edges[stack[-1]].pop())
            else:route.append(stack.pop())
        route.reverse()
        self.assertEqual(len(set(zip(route, route[1:]))), 20)
        sim = r9()
        self.run_segment(sim, 'stop', 2.)
        for command in route:self.run_segment(sim, command, 1.14)
        self.run_segment(sim, 'stop', 3.)
        self.assertEqual(sim.reference.mode, 'stand')


if __name__ == '__main__':unittest.main()
