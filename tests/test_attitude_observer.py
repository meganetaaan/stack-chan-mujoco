import unittest
import mujoco
import numpy as np
from stackchan_rl.attitude_observer import AttitudeObserver
from stackchan_rl.residual import STATE_SPEC


class AttitudeObserverTests(unittest.TestCase):
    def setUp(self):
        self.model=mujoco.MjModel.from_xml_string('<mujoco><worldbody><body name="base"><freejoint/><geom type="sphere" size=".1" mass="1"/></body></worldbody></mujoco>')
        self.data=mujoco.MjData(self.model);mujoco.mj_forward(self.model,self.data)
        self.base=self.model.body('base').id
        self.zero={'gravity_noise_std':0.,'gyro_noise_std_rad_s':0.,'gyro_bias_std_rad_s':0.}

    def state(self):
        s=np.empty(mujoco.mj_stateSize(self.model,STATE_SPEC));mujoco.mj_getState(self.model,self.data,s,STATE_SPEC);return s

    def test_one_sample_delay_and_no_state_mutation(self):
        observer=AttitudeObserver(self.model,self.data,self.base,self.zero,310701)
        angle=.2;self.data.qpos[3:7]=[np.cos(angle/2),np.sin(angle/2),0,0]
        self.data.qvel[3:]=[.3,0,0];mujoco.mj_forward(self.model,self.data)
        before=self.state()
        np.testing.assert_allclose(observer.read(),[0,0,-1,0,0,0],atol=1e-14)
        np.testing.assert_allclose(observer.read(),[0,-np.sin(angle),-np.cos(angle),.3,0,0],atol=1e-14)
        np.testing.assert_array_equal(self.state(),before)
        self.assertEqual(observer.metadata()['effective_delay_s'],.02)

    def test_seeded_noise_and_unit_gravity(self):
        p={'gravity_noise_std':.004,'gyro_noise_std_rad_s':.02,'gyro_bias_std_rad_s':.005}
        a=AttitudeObserver(self.model,self.data,self.base,p,310702)
        b=AttitudeObserver(self.model,self.data,self.base,p,310702)
        for _ in range(10):
            x=a.read();np.testing.assert_array_equal(x,b.read());self.assertEqual(x.shape,(6,));self.assertAlmostEqual(np.linalg.norm(x[:3]),1.)


if __name__=='__main__':unittest.main()
