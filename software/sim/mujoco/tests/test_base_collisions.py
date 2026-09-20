import json
from pathlib import Path
import unittest
import mujoco
import numpy as np
from stackchan_rl.residual import runtime_xml

class AddedBaseCollisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old=mujoco.MjModel.from_xml_string(runtime_xml(Path('assets/r6_rear_bridge8_collision/models/scene.xml')))
        cls.new=mujoco.MjModel.from_xml_string(runtime_xml(Path('assets/r6_base_collisions/models/scene.xml')))
    def test_physical_parameters_unchanged(self):
        for name in ['body_mass','body_inertia','body_ipos','body_iquat','jnt_range','jnt_axis','jnt_pos',
                     'actuator_ctrlrange','actuator_forcerange','actuator_gear','dof_damping','dof_frictionloss','dof_armature']:
            np.testing.assert_array_equal(getattr(self.old,name),getattr(self.new,name),err_msg=name)
        self.assertEqual(self.new.ngeom-self.old.ngeom,22)
    def test_cad_confirmed_contact_detected(self):
        pose=json.loads(Path('validation/base_collisions/positive_pose.json').read_text())
        d=mujoco.MjData(self.new);d.qpos[:]=pose['qpos'];mujoco.mj_forward(self.new,d)
        names=set(pose['pair'])
        contacts=[c for c in d.contact if {self.new.geom(c.geom1).name,self.new.geom(c.geom2).name}==names]
        self.assertTrue(contacts);self.assertLess(min(c.dist for c in contacts),-.001)
        cad=json.loads(Path('validation/base_collisions/positive_pose_cad.json').read_text())
        self.assertTrue(any({f['a'],f['b']}=={'left_fixed_roll_cradle','left_knee_motor'} and f['overlap_mm3']>.01
                            for f in cad['results'][0]['findings']))

if __name__=='__main__':unittest.main()
