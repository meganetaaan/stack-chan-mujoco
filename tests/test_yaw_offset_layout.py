import json
from pathlib import Path
import unittest
import mujoco
import numpy as np
from stackchan_rl.residual import runtime_xml
from audit_yaw_layout import audit


class CorrectedYawLayoutTests(unittest.TestCase):
    path=Path('assets/r8_yaw_offset_flange_v1')

    def test_external_geometry_and_kinematics_preserved(self):
        old=Path('assets/r7_yaw_xc_ankles_v1')
        a=mujoco.MjModel.from_xml_string(runtime_xml(old/'models/scene.xml'))
        b=mujoco.MjModel.from_xml_string(runtime_xml(self.path/'models/scene.xml'))
        for name in ['body_pos','jnt_pos','jnt_axis','jnt_range','actuator_ctrlrange']:
            np.testing.assert_allclose(getattr(a,name),getattr(b,name),atol=1e-12,rtol=0)
        for i in range(a.ngeom):
            name=a.geom(i).name
            if any(x in name for x in ['sole_TPU','Tab5','body_shroud','foot_yoke']):
                j=b.geom(name).id
                for attr in ['geom_pos','geom_size','geom_quat']:
                    np.testing.assert_array_equal(getattr(a,attr)[i],getattr(b,attr)[j])
        self.assertEqual((b.nq,b.nv,b.nu,b.neq),(19,18,12,0))
        np.testing.assert_array_equal(b.body_gravcomp,0)

    def test_shaft_offset_and_motor_mass_split(self):
        m=mujoco.MjModel.from_xml_string(runtime_xml(self.path/'models/scene.xml'))
        r=json.loads((self.path/'CANDIDATE.json').read_text())
        self.assertAlmostEqual(m.body_mass.sum(),r['total_mass_kg'],places=12)
        for side in ['left','right']:
            case=m.geom('col_'+side+'_yaw_motor_case')
            np.testing.assert_allclose(case.size,[.017,.010,.0115],atol=1e-12)
            self.assertAlmostEqual(m.body(side+'_hip_yaw').pos[0]-case.pos[0],.0075)
            horn=m.geom('col_'+side+'_yaw_motor_horn')
            self.assertEqual(m.geom_bodyid[horn.id],m.body(side+'_hip_yaw').id)
            fixed=next(x for x in r['fixed_base_parts'] if x['part']==side+'_yaw_motor_case')
            moving=next(x for x in r['new_yaw_link_parts'] if x['part']==side+'_yaw_motor_horn')
            self.assertAlmostEqual(fixed['mass_kg']+moving['mass_kg'],.018,places=12)

    def test_mount_sweep_and_known_leg_collision_are_reported(self):
        report=audit(self.path)
        self.assertTrue(report['parent_filter_disabled'])
        self.assertEqual(report['home_penetrations'],[])
        self.assertEqual(report['yaw_mount_penetration_pairs'],[])
        self.assertGreater(report['failed_samples'],0)
        self.assertIn('col_left_sole_TPU_0 / col_right_sole_TPU_0',report['worst_by_pair'])


if __name__=='__main__':unittest.main()
