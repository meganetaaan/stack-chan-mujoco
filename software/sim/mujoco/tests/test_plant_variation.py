"""Perturb the physical plant consistently, including derived mass and contact friction."""
import unittest
import numpy as np
import mujoco
from plant_variation import validate_variation, vary_model, vary_motors


class PlantVariationTests(unittest.TestCase):
    def model(self):
        return mujoco.MjModel.from_xml_string('''<mujoco>
          <worldbody><geom name="floor" type="plane" size="1 1 .1" friction=".8 .003 .001"/>
            <body pos="0 0 .09"><joint name="joint" type="hinge"/>
              <geom type="box" size=".1 .1 .1" mass="1" friction=".8 .003 .001"/>
            </body></worldbody>
          <actuator><motor joint="joint" ctrlrange="-1 1" forcerange="-1 1"/></actuator>
        </mujoco>''')

    def test_mass_constants_and_actual_combined_contact_friction_change(self):
        m = self.model();d = mujoco.MjData(m)
        old_inertia = m.body_inertia.copy()
        v = validate_variation({'mass_scale':1.05,'sliding_friction':.6})
        vary_model(m,d,v);mujoco.mj_forward(m,d)
        self.assertAlmostEqual(m.body_mass[1],1.05)
        self.assertAlmostEqual(m.body_subtreemass[0],1.05)
        np.testing.assert_allclose(m.body_inertia,old_inertia*1.05)
        self.assertGreater(d.ncon,0)
        self.assertAlmostEqual(d.contact[0].friction[0],.6)

    def test_motor_and_engine_limits_remain_consistent(self):
        m = self.model()
        motor = {k:np.array([v]) for k,v in {'cap':1.,'stall':2.,'omega':10.,'delay_s':.01}.items()}
        v = validate_variation({'torque_scale':.9,'speed_scale':.95,'extra_delay_s':.004})
        vary_motors(m,motor,np.array([0]),v)
        np.testing.assert_allclose(motor['cap'],[.9])
        np.testing.assert_allclose(motor['stall'],[1.8])
        np.testing.assert_allclose(motor['omega'],[9.5])
        np.testing.assert_allclose(motor['delay_s'],[.014])
        np.testing.assert_allclose(m.actuator_ctrlrange,[[-.9,.9]])
        np.testing.assert_allclose(m.actuator_forcerange,[[-.9,.9]])

    def test_invalid_variations_are_rejected(self):
        for value in [{'mass_scale':True},{'torque_scale':float('nan')},{'unknown':1},
                      {'initial_joint_offset_rad':[0.]},{'sliding_friction':-1}]:
            with self.subTest(value=value),self.assertRaises(ValueError):
                validate_variation(value)


if __name__ == '__main__':
    unittest.main()
