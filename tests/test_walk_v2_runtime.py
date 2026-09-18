"""Actual engine/SB3 checks. Never substitute synthetic physics for missing deps."""
from __future__ import annotations
import importlib.util
from pathlib import Path
import tempfile
import unittest
import numpy as np
from stackchan_rl.config import ROOT, load_config

AVAILABLE=all(importlib.util.find_spec(n) for n in ('mujoco','gymnasium','stable_baselines3'))

@unittest.skipUnless(AVAILABLE,'MuJoCo/Gymnasium/SB3 missing: v2 runtime NOT EXECUTED')
class WalkV2RuntimeTests(unittest.TestCase):
    def setUp(self):
        from stackchan_rl.env import StackChanEnv
        self.cfg=load_config(ROOT/'configs/walk_smoke.json')
        self.env=StackChanEnv(self.cfg)
    def tearDown(self):self.env.close()

    def test_contract_v2(self):
        from stable_baselines3.common.env_checker import check_env
        check_env(self.env,warn=True,skip_render_check=True)

    def test_v2_episode_reports_event_diagnostics(self):
        self.env.reset(seed=50)
        for _ in range(self.env.max_steps):
            _,r,t,tr,info=self.env.step(np.zeros(10,dtype=np.float32))
            self.assertTrue(np.isfinite(r))
            if t or tr:
                s=info['episode_summary']
                self.assertIn('forward_landings',s);self.assertIn('qualified_liftoffs',s)
                self.assertIn('behavior',s);self.assertIn('event_rejections',s);break
        else:self.fail('Expected episode completion')

    def test_csv_columns_stable_from_reset_through_rollout(self):
        self.env.reset(seed=51);cols=set(self.env.trajectory_row())
        for _ in range(self.env.max_steps):
            _,_,t,tr,_=self.env.step(np.zeros(10,dtype=np.float32))
            self.assertEqual(cols,set(self.env.trajectory_row()))
            if t or tr:break

    def test_actor_transfer_on_actual_SB3_MlpPolicy(self):
        from stable_baselines3 import PPO
        import torch
        from stackchan_rl.transfer import transfer_policy
        torch.set_num_threads(1)
        kwargs=dict(policy_kwargs={'net_arch':{'pi':[64,64],'vf':[64,64]}},device='cpu',n_steps=32,batch_size=32,n_epochs=1)
        a=PPO('MlpPolicy',self.env,seed=1,**kwargs);b=PPO('MlpPolicy',self.env,seed=2,**kwargs)
        obs,_=self.env.reset(seed=7)
        before=b.policy.value_net.weight.detach().clone()
        x=a.predict(obs,deterministic=True)[0]
        transfer_policy(a.policy,b.policy,actor_only=True,reset_log_std=-1.)
        np.testing.assert_allclose(x,b.predict(obs,deterministic=True)[0],atol=1e-6)
        torch.testing.assert_close(before,b.policy.value_net.weight)
        torch.testing.assert_close(b.policy.log_std,torch.full((10,),-1.))

    def test_short_v2_PPO_and_saved_evaluation(self):
        from stable_baselines3 import PPO
        from stackchan_rl.checkpoints import save_bundle,bundle_info,assert_interface
        from stackchan_rl.evaluation import evaluate_agent
        import torch
        torch.set_num_threads(1)
        p=PPO('MlpPolicy',self.env,n_steps=32,batch_size=32,n_epochs=1,device='cpu',seed=3)
        p.learn(64)
        with tempfile.TemporaryDirectory() as t:
            save_bundle(p,Path(t)/'bundle',self.cfg,self.env.specification.interface(self.cfg))
            folder,cfg,interface,_=bundle_info(Path(t)/'bundle');assert_interface(interface,cfg)
            q=PPO.load(str(folder/'model.zip'),device='cpu')
            result=evaluate_agent(q,cfg,1,123,command=.02,trajectory_dir=Path(t)/'csv')
            self.assertEqual(len(result['selection_key']),6)
            self.assertTrue(result['physics_executed']);self.assertEqual(result['episodes'],1)
