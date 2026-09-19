import json
from pathlib import Path
import unittest
import mujoco
import numpy as np
from stackchan_rl.residual import ResidualEnv,SaturationProtection,STATE_SPEC

class ProtectionTests(unittest.TestCase):
    def make(self):
        return SaturationProtection(.001,{'continuous_saturation_s':.25,'saturation_window_s':1.,'saturation_duty_limit':.5})
    def test_continuous_trip(self):
        p=self.make();a=np.zeros(10,dtype=bool);a[2]=True
        for _ in range(249):self.assertIsNone(p.update(a))
        self.assertEqual(p.update(a),'continuous_saturation')
    def test_window_not_reset_by_short_gaps(self):
        p=self.make()
        for i in range(999):self.assertIsNone(p.update(np.full(10,i%10<6)))
        self.assertEqual(p.update(np.full(10,False)),'saturation_duty')
    def test_short_pulses_allowed(self):
        p=self.make()
        for i in range(1200):self.assertIsNone(p.update(np.full(10,i%100<10)))

@unittest.skipUnless(Path('outputs/design_r6_rear_bridge8_collision/models/scene.xml').exists(),'build R6 design first')
class ResidualPhysicsTests(unittest.TestCase):
    def make(self,randomize=False,record=False):
        c=json.loads(Path('configs/r6_residual.json').read_text());c['randomize']=randomize
        return ResidualEnv(c,record=record)
    def test_real_state_replay_and_collision_meshes(self):
        e=self.make(record=True);e.reset(seed=71)
        self.assertEqual(e.model.nmesh,508)
        for _ in range(10):e.step(np.ones(10)*.05)
        q=e.data.qpos.copy();v=e.data.qvel.copy()
        state=e.get_state();e.data.qpos[:3]+=10
        mujoco.mj_setState(e.model,e.data,state,STATE_SPEC);mujoco.mj_forward(e.model,e.data)
        np.testing.assert_array_equal(e.data.qpos,q);np.testing.assert_array_equal(e.data.qvel,v)
        self.assertTrue(np.all(e.data.xfrc_applied==0));self.assertTrue(np.all(e.data.qfrc_applied==0))
    def test_seed_replays_noise_and_randomized_plant(self):
        e=self.make(True)
        o,info=e.reset(seed=17);q=e.model.body_ipos.copy();mass=e.model.body_mass.copy()
        states=[]
        for _ in range(5):states.append(e.step(np.zeros(10))[0])
        again,other=e.reset(seed=17)
        np.testing.assert_array_equal(o,again);self.assertEqual(info['parameters'],other['parameters'])
        np.testing.assert_array_equal(e.model.body_ipos,q);np.testing.assert_array_equal(e.model.body_mass,mass)
        for expected in states:np.testing.assert_array_equal(e.step(np.zeros(10))[0],expected)
        different,_=e.reset(seed=18);self.assertFalse(np.array_equal(o,different))
    def test_joint_limit_is_latched(self):
        e=self.make();e.reset(seed=1)
        e.data.qpos[e.qadr[0]]=e.limits[0,1]+.001
        mujoco.mj_forward(e.model,e.data)
        self.assertEqual(e._check_physics(),'joint_limit')
    def test_action_changes_physics_and_noise_is_enabled_in_fixed_case(self):
        e=self.make();o,info=e.reset(seed=1)
        for _ in range(20):e.step(np.zeros(10))
        state=e.data.qpos.copy()
        other,_=e.reset(seed=2);self.assertFalse(np.array_equal(o,other))
        for _ in range(20):e.step(np.ones(10)*.5)
        self.assertGreater(np.max(np.abs(e.data.qpos-state)),1e-5)
        self.assertGreater(info['parameters']['gyro_noise_std_rad_s'],0)

if __name__=='__main__':unittest.main()
