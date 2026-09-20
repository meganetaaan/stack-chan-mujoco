import unittest
import mujoco
import numpy as np
from teleop_yaw import requested_command, Simulation, ROOT


class KeyboardTests(unittest.TestCase):
    def test_release_and_space_stop(self):
        self.assertEqual(requested_command(set()),'stop')
        self.assertEqual(requested_command({'W','SPACE'}),'stop')

    def test_directions_and_opposites(self):
        for key,name in [('W','forward'),('S','backward'),('A','left'),('D','right')]:
            self.assertEqual(requested_command({key}),name)
        self.assertEqual(requested_command({'W','S'}),'stop')
        self.assertEqual(requested_command({'A','D'}),'stop')

    def test_cached_physics_matches_original_step(self):
        models=[Simulation(ROOT/'design/teleop_reference',ROOT/'assets/r8_yaw_offset_flange_v1') for _ in range(2)]
        models[0].advance=mujoco.mj_step
        for _ in range(200):
            for sim in models:sim.step('forward')
            np.testing.assert_array_equal(models[0].d.qpos,models[1].d.qpos)
            np.testing.assert_array_equal(models[0].d.qvel,models[1].d.qvel)
            self.assertEqual(models[0].failure,models[1].failure)
        self.assertIsNone(models[1].failure)

    def test_command_change_does_not_restart_airborne_step(self):
        sim=Simulation(ROOT/'design/teleop_reference',ROOT/'assets/r8_yaw_offset_flange_v1')
        ref=sim.reference
        ref.set_command('forward',0.)
        ref.sample(0.)
        end=ref.end
        ref.set_command('backward',.02)
        ref.sample(.02)
        self.assertEqual(ref.end,end)
        ref.sample(end)
        self.assertLess(ref.target_x-ref.feet[ref.stance,0],0.)


if __name__=='__main__':unittest.main()
