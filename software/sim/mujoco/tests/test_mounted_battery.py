import json
from pathlib import Path
import unittest
import mujoco
import numpy as np

ROOT=Path(__file__).resolve().parents[1]


class MountedBatteryTests(unittest.TestCase):
    def test_only_base_dynamics_changes(self):
        old=mujoco.MjModel.from_xml_path(str(ROOT/'assets/r6_base_collisions/models/scene.xml'))
        new=mujoco.MjModel.from_xml_path(str(ROOT/'assets/r6_mounted_battery/models/scene.xml'))
        self.assertEqual((new.nq,new.nv,new.nu),(17,16,10))
        for name in ('jnt_axis','jnt_pos','jnt_range','actuator_gear','actuator_ctrlrange','actuator_forcerange','dof_damping','dof_frictionloss','dof_armature','body_pos','body_quat'):
            np.testing.assert_array_equal(getattr(old,name),getattr(new,name),err_msg=name)
        base=new.body('base').id
        for name in ('body_mass','body_inertia','body_ipos','body_iquat'):
            np.testing.assert_array_equal(np.delete(getattr(old,name),base,axis=0),np.delete(getattr(new,name),base,axis=0))
        delta=json.loads((ROOT/'assets/r6_mounted_battery/BATTERY_MOUNT_PATCH.json').read_text())['total_mass_delta_kg']
        self.assertAlmostEqual(float(new.body_mass.sum()-old.body_mass.sum()),delta,places=11)
        self.assertGreater(delta,.01)

    def test_compiled_collision_coverage_and_battery_position(self):
        from stackchan_rl.residual import runtime_xml
        m=mujoco.MjModel.from_xml_string(runtime_xml(ROOT/'assets/r6_mounted_battery/models/scene.xml',False))
        np.testing.assert_allclose(m.geom('col_battery_2S_reservation_0').pos,[-.001,0,.080],atol=1e-12)
        self.assertTrue(m.geom('col_battery_tray_0').contype)
        for i in range(6): self.assertTrue(m.geom(f'col_battery_strap_{i}').contype)
        for i in range(2): self.assertTrue(m.geom(f'col_battery_M3_envelope_{i}_0').contype)
        np.testing.assert_array_equal(m.opt.gravity,[0,0,-9.81])
        self.assertEqual(m.neq,0)
        self.assertFalse(np.any(m.body_gravcomp))


if __name__=='__main__': unittest.main()
