import json
from pathlib import Path
import unittest
import mujoco
import numpy as np
from stackchan_rl.residual import runtime_xml
from probe_yaw_dynamics_candidate import JointProtection


class CandidateModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path=Path('assets/r7_yaw_candidate_v1')
        if not cls.path.exists():cls.path=Path('outputs/yaw_dynamics_candidate_v3')
        if not cls.path.exists():raise unittest.SkipTest('build yaw dynamics candidate first')
        cls.model=mujoco.MjModel.from_xml_string(runtime_xml(cls.path/'models/scene.xml'))

    def test_mass_accounting_and_unassisted_twelve_axis_model(self):
        m=self.model
        self.assertEqual((m.nq,m.nv,m.nu,m.neq),(19,18,12,0))
        np.testing.assert_array_equal(m.opt.gravity,[0,0,-9.81])
        np.testing.assert_array_equal(m.body_gravcomp,0.)
        report=json.loads((self.path/'CANDIDATE.json').read_text())
        self.assertAlmostEqual(m.body_mass.sum(),report['total_mass_kg'],places=12)
        self.assertAlmostEqual(sum(r['mass_kg'] for r in report['fixed_base_parts']),m.body('base').mass[0],places=12)
        for side in ('left','right'):
            mass=sum(r['mass_kg'] for r in report['new_yaw_link_parts'] if r['part'].startswith(side+'_'))
            self.assertAlmostEqual(mass,m.body(side+'_hip_yaw').mass[0],places=12)
        self.assertTrue(np.all(m.body_inertia[1:]>0))

    def test_zero_yaw_home_preserves_old_link_geometry_and_motor_limits(self):
        old=mujoco.MjModel.from_xml_string(runtime_xml(Path('assets/r6_mounted_battery/models/scene.xml')))
        before=mujoco.MjData(old);after=mujoco.MjData(self.model)
        mujoco.mj_resetDataKeyframe(old,before,0);mujoco.mj_forward(old,before)
        mujoco.mj_resetDataKeyframe(self.model,after,0);mujoco.mj_forward(self.model,after)
        for i in range(1,old.nbody):
            name=old.body(i).name;j=self.model.body(name).id
            np.testing.assert_allclose(before.xpos[i],after.xpos[j],atol=1e-12,rtol=0)
            np.testing.assert_allclose(before.xmat[i],after.xmat[j],atol=1e-12,rtol=0)
        for i in range(old.nu):
            name=old.actuator(i).name;j=self.model.actuator(name).id
            np.testing.assert_array_equal(old.actuator_ctrlrange[i],self.model.actuator_ctrlrange[j])

    def test_no_initial_self_penetration_and_parent_contacts_not_filtered(self):
        m=self.model;d=mujoco.MjData(m);mujoco.mj_resetDataKeyframe(m,d,0);mujoco.mj_forward(m,d)
        floor=m.geom('floor').id
        self.assertTrue(m.opt.disableflags & int(mujoco.mjtDisableBit.mjDSBL_FILTERPARENT))
        self.assertEqual(m.npair,0)
        for contact in d.contact:
            if floor not in (contact.geom1,contact.geom2):
                self.assertGreaterEqual(contact.dist,-1e-8,(m.geom(contact.geom1).name,m.geom(contact.geom2).name))

    def test_joint_map_coordinates_match_mjcf_parent_frames(self):
        for entry in json.loads((self.path/'models/joint_map.json').read_text()):
            joint=self.model.joint(entry['name'])
            body=self.model.jnt_bodyid[joint.id]
            np.testing.assert_allclose(entry['origin_m'],self.model.body_pos[body],atol=1e-12,rtol=0)
            np.testing.assert_allclose(entry['axis'],self.model.jnt_axis[joint.id],atol=1e-12,rtol=0)


class TwelveJointProtectionTests(unittest.TestCase):
    def test_all_twelve_channels_including_last_are_protected(self):
        cfg={'continuous_saturation_s':.25,'saturation_window_s':1.,'saturation_duty_limit':.5}
        protection=JointProtection(.001,cfg,12)
        saturated=np.zeros(12,dtype=bool);saturated[11]=True
        for _ in range(249):self.assertIsNone(protection.update(saturated))
        self.assertEqual(protection.update(saturated),'continuous_saturation')
        self.assertEqual(protection.peak_streak[11],250)
        np.testing.assert_array_equal(protection.peak_streak[:11],0)


if __name__=='__main__':unittest.main()
