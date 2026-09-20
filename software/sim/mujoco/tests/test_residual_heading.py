import json
from pathlib import Path
import unittest
import mujoco
import numpy as np
from stackchan_rl.residual import ResidualEnv
from stackchan_rl.residual_heading import HeadingResidualEnv

@unittest.skipUnless(Path('outputs/design_r6_rear_bridge8_collision/models/scene.xml').exists(),'build R6 design first')
class HeadingObservationTests(unittest.TestCase):
    def config(self):return json.loads(Path('configs/r6/heading_residual.json').read_text())
    def test_zero_action_physics_unchanged(self):
        c=self.config();c['randomize']=False
        v2=HeadingResidualEnv(c);c1={**c,'schema':'r6-residual-v1'};v1=ResidualEnv(c1)
        a,_=v2.reset(seed=13);v1.reset(seed=13)
        self.assertEqual(a.shape,(70,))
        for _ in range(60):
            v1.step(np.zeros(10));v2.step(np.zeros(10))
        np.testing.assert_array_equal(v1.data.qpos,v2.data.qpos)
        np.testing.assert_array_equal(v1.data.qvel,v2.data.qvel)
    def test_yaw_becomes_observable(self):
        c=self.config();c['randomize']=False;e=HeadingResidualEnv(c)
        obs,_=e.reset(seed=42)
        e.data.qpos[3:7]=[np.cos(.15),0,0,np.sin(.15)]
        mujoco.mj_forward(e.model,e.data);turned=e._observation()
        self.assertGreater(turned[65]-obs[65],.25)
        self.assertLess(np.linalg.norm(turned[30:33]-obs[30:33]),.02)
    def test_noise_and_parameters_replay(self):
        e=HeadingResidualEnv(self.config());obs,info=e.reset(seed=88)
        again,other=e.reset(seed=88)
        np.testing.assert_array_equal(obs,again);self.assertEqual(info,other)
        self.assertGreater(info['parameters']['external_heading_std_rad'],0)
        self.assertNotEqual(e.fingerprint['schema'],'r6-residual-v1')


@unittest.skipUnless(Path('policies/r6_residual_seed20260920/policy.zip').exists(),'published parent required')
class TransferTests(unittest.TestCase):
    def test_transfer_preserves_actor_and_value_function(self):
        import torch
        from stable_baselines3 import PPO
        from train_heading_residual import transfer_policy
        torch.set_num_threads(1)
        c=json.loads(Path('configs/r6/heading_residual.json').read_text());e=HeadingResidualEnv(c)
        parent=PPO.load('policies/r6_residual_seed20260920/policy',device='cpu')
        model=PPO('MlpPolicy',e,device='cpu',policy_kwargs={'net_arch':dict(pi=[64,64],vf=[64,64])})
        transfer_policy(parent,model)
        obs=np.random.default_rng(23).normal(size=(12,70)).astype(np.float32)
        np.testing.assert_allclose(model.predict(obs,deterministic=True)[0],parent.predict(obs[:,:65],deterministic=True)[0],atol=1e-7)
        with torch.no_grad():
            new_value=model.policy.predict_values(torch.as_tensor(obs))
            old_value=parent.policy.predict_values(torch.as_tensor(obs[:,:65]))
        np.testing.assert_allclose(new_value.numpy(),old_value.numpy(),atol=1e-6)

if __name__=='__main__':unittest.main()
