import json
from pathlib import Path
import unittest
import numpy as np
import mujoco
from stackchan_rl.candidate_variation import sample_parameters,apply_parameters
from stackchan_rl.residual import runtime_xml
from stackchan_rl.residual_heading import HeadingResidualEnv


class CandidateVariationTests(unittest.TestCase):
    def setUp(self):
        self.config=json.loads(Path('policies/r6_mounted_seed20260924/config.json').read_text())

    def test_matches_original_ten_axis_parameter_draws(self):
        env=HeadingResidualEnv(self.config)
        try:
            env.reset(seed=310601,options={'randomize':True})
            p=sample_parameters(self.config,np.random.default_rng(310601),True,.8,10)
            for key,value in p.items():np.testing.assert_array_equal(value,env.parameters[key])
        finally:env.close()

    def test_all_twelve_channels_and_both_contact_surfaces_change(self):
        model=mujoco.MjModel.from_xml_string(runtime_xml(Path('assets/r7_yaw_xc_ankles_v1/models/scene.xml')))
        data=mujoco.MjData(model);base=model.body('base').id
        mass=model.body_mass.copy();inertia=model.body_inertia.copy();com=model.body_ipos.copy();ctrl=model.actuator_ctrlrange.copy()
        motor={key:np.ones(12) for key in ('cap','stall','omega','delay_s')}
        p=sample_parameters(self.config,np.random.default_rng(310602),True,.8,12)
        varied=apply_parameters(model,data,motor,np.arange(12),base,p)
        self.assertEqual(len(p['initial_joint_offsets_rad']),12)
        np.testing.assert_allclose(model.body_mass,mass*p['mass_scale'])
        np.testing.assert_allclose(model.body_inertia,inertia*p['mass_scale'])
        np.testing.assert_allclose(model.body_ipos[base]-com[base],p['base_com_shift_m'])
        np.testing.assert_allclose(model.geom_friction[:,0],p['friction'])
        np.testing.assert_allclose(model.actuator_ctrlrange,ctrl*p['torque_scale'])
        np.testing.assert_allclose(varied['cap'],p['torque_scale'])
        np.testing.assert_array_equal(motor['cap'],np.ones(12))
        np.testing.assert_allclose(varied['delay_s'],1+p['extra_delay_s'])

    def test_fixed_condition_preserves_nominal_contact_and_motor_parameters(self):
        model=mujoco.MjModel.from_xml_string(runtime_xml(Path('assets/r7_yaw_xc_ankles_v1/models/scene.xml')))
        data=mujoco.MjData(model)
        names=('body_mass','body_inertia','body_ipos','geom_friction','actuator_ctrlrange','actuator_forcerange')
        before={name:getattr(model,name).copy() for name in names}
        motor={key:np.linspace(.2,.9,12) for key in ('cap','stall','omega','delay_s')}
        p=sample_parameters(self.config,np.random.default_rng(310603),False,.9,12)
        varied=apply_parameters(model,data,motor,np.arange(12),model.body('base').id,p)
        for name in names:np.testing.assert_array_equal(getattr(model,name),before[name])
        for key in motor:np.testing.assert_array_equal(varied[key],motor[key])


if __name__=='__main__':unittest.main()
