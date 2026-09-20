import json
from pathlib import Path
import unittest
import mujoco
import numpy as np
from stackchan_rl.residual import runtime_xml


class AnkleUpgradeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path=Path('assets/r7_yaw_xc_ankles_v1')
        if not cls.path.exists():cls.path=Path('outputs/yaw_xc_ankles_v1')
        if not cls.path.exists():raise unittest.SkipTest('build upgraded candidate first')
        cls.old=mujoco.MjModel.from_xml_string(runtime_xml(Path('assets/r7_yaw_candidate_v1/models/scene.xml')))
        cls.new=mujoco.MjModel.from_xml_string(runtime_xml(cls.path/'models/scene.xml'))

    def test_mass_increases_only_on_the_two_motor_carrying_links(self):
        self.assertAlmostEqual(self.new.body_mass.sum()-self.old.body_mass.sum(),.01,places=12)
        for i in range(1,self.old.nbody):
            name=self.old.body(i).name;j=self.new.body(name).id
            expected=.005 if name in ('left_knee','right_knee') else 0.
            self.assertAlmostEqual(self.new.body_mass[j]-self.old.body_mass[i],expected,places=12)
            if expected:self.assertFalse(np.array_equal(self.new.body_inertia[j],self.old.body_inertia[i]))

    def test_collision_geometry_and_other_torque_caps_unchanged(self):
        for name in ('geom_pos','geom_quat','geom_size','geom_friction','geom_contype','geom_conaffinity'):
            np.testing.assert_array_equal(getattr(self.old,name),getattr(self.new,name))
        for i in range(self.old.nu):
            name=self.old.actuator(i).name;j=self.new.actuator(name).id
            expected=[-.45,.45] if name in ('left_ankle_pitch_motor','right_ankle_pitch_motor') else self.old.actuator_ctrlrange[i]
            np.testing.assert_array_equal(self.new.actuator_ctrlrange[j],expected)

    def test_motor_inventory_and_speed_are_updated_together(self):
        r=json.loads((self.path/'robot.json').read_text())
        self.assertEqual(r['motor']['quantity'],6)
        self.assertEqual(r['motor_overrides']['quantity'],6)
        self.assertIn('ankle_pitch',r['motor_overrides']['joint_types'])
        self.assertEqual(r['motor_overrides']['no_load_speed_rpm'],81)
        self.assertEqual(r['motor_overrides']['mass_kg'],.023)


if __name__=='__main__':unittest.main()
