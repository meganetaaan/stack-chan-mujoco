"""Real MuJoCo/SB3 paths. Dependency absence means SKIP, never a fake pass."""
from __future__ import annotations
from copy import deepcopy
import importlib.util
from pathlib import Path
import tempfile
import unittest
import numpy as np
from stackchan_rl.config import ROOT, load_config
AVAILABLE = all(importlib.util.find_spec(n) is not None for n in ('mujoco','gymnasium','stable_baselines3'))


@unittest.skipUnless(AVAILABLE, 'MuJoCo/Gymnasium/SB3 missing: v4 runtime NOT EXECUTED')
class LP40Runtime(unittest.TestCase):
    def setUp(self):
        from stackchan_rl.env import StackChanEnv
        self.cfg=load_config(ROOT/'configs/lp40_smoke.json')
        self.env=StackChanEnv(self.cfg)
    def tearDown(self):self.env.close()
    def test_sb3_contract(self):
        from stable_baselines3.common.env_checker import check_env
        check_env(self.env,warn=True,skip_render_check=True)
    def test_observation_is_post_filter_pre_delay(self):
        self.env.reset(seed=7,options={'no_noise':True})
        obs,*_=self.env.step(np.full(10,.4))
        expected=(self.env.bank.filtered-self.env.home_joints)/self.env.action_scale
        np.testing.assert_allclose(obs[39:49],expected,atol=1e-7)
        np.testing.assert_allclose(obs[29:39],.4,atol=1e-7)
        self.assertFalse(np.allclose(self.env.bank.slew_stage,self.env.bank.filtered))
    def test_production_matches_original_probe_physics_and_observation(self):
        from stackchan_rl.env import StackChanEnv
        from tests._probe_reference import PostSlewLowPassBank
        c=load_config(ROOT/'configs/walk_lp40_baseline.json');c['env']['episode_seconds']=1.
        a=StackChanEnv(c);c['env']['target_lowpass_time_constant_s']=0.;b=StackChanEnv(c)
        b.bank=PostSlewLowPassBank(b.specification.motor,float(b.model.opt.timestep),2.,.04)
        try:
            oa,_=a.reset(seed=47);ob,_=b.reset(seed=47)
            np.testing.assert_array_equal(oa,ob)
            rng=np.random.default_rng(71)
            for _ in range(50):
                action=rng.uniform(-.2,.2,10)
                oa,ra,ta,tra,_=a.step(action);ob,rb,tb,trb,_=b.step(action)
                np.testing.assert_allclose(a.data.qpos,b.data.qpos,atol=1e-13,rtol=0)
                np.testing.assert_allclose(a.data.qvel,b.data.qvel,atol=1e-13,rtol=0)
                np.testing.assert_array_equal(oa,ob)
                self.assertAlmostEqual(ra,rb,places=12);self.assertEqual((ta,tra),(tb,trb))
                if ta or tra:break
        finally:a.close();b.close()
    def test_reset_repeatability_clears_all_stages(self):
        oa,_=self.env.reset(seed=9);x=self.env.step(np.ones(10)*.1)
        ob,_=self.env.reset(seed=9);y=self.env.step(np.ones(10)*.1)
        np.testing.assert_array_equal(oa,ob);np.testing.assert_array_equal(x[0],y[0])
        self.assertEqual(x[1],y[1])
    def test_csv_schema_and_new_metrics(self):
        self.env.reset(seed=7);keys=set(self.env.trajectory_row())
        self.assertIn('policy_input_60',keys);self.assertIn('left_knee_slew_target_rad',keys)
        for _ in range(self.env.max_steps):
            _,_,t,tr,info=self.env.step(np.zeros(10));self.assertEqual(keys,set(self.env.trajectory_row()))
            if t or tr:
                s=info['episode_summary'];self.assertGreater(s['target_metric_samples'],0)
                self.assertIn('terminal_self_contact_pairs',s)
                self.assertIn('ordered_forward_landings',s)
                self.assertIn('distance_tracking',s['quality_checks']);break
    def test_true_sb3_transfer_save_load_resume(self):
        import torch
        from stable_baselines3 import PPO
        from stackchan_rl.checkpoints import save_bundle,bundle_info,assert_interface
        torch.set_num_threads(1)
        agent=PPO('MlpPolicy',self.env,n_steps=32,batch_size=32,n_epochs=1,device='cpu',seed=27)
        agent.learn(32)
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'bundle';save_bundle(agent,path,self.cfg,self.env.specification.interface(self.cfg))
            p,c,iface,_=bundle_info(path);assert_interface(iface,c)
            self.assertEqual(c['env']['target_lowpass_time_constant_s'],.04)
            loaded=PPO.load(str(p/'model.zip'),env=self.env,device='cpu',force_reset=True)
            obs,_=self.env.reset(seed=8)
            np.testing.assert_allclose(agent.predict(obs,deterministic=True)[0],loaded.predict(obs,deterministic=True)[0],atol=1e-7)
            loaded.learn(32,reset_num_timesteps=False)
            self.assertGreaterEqual(loaded.num_timesteps,64)
    def test_legacy_actor_preserved_new_critic_new_filter(self):
        import torch
        from stable_baselines3 import PPO
        from stackchan_rl.env import StackChanEnv
        from stackchan_rl.transfer import transfer_policy
        from stackchan_rl.checkpoints import assert_transfer_interface
        torch.set_num_threads(1)
        c=load_config(ROOT/'configs/refine_smoke.json');old=StackChanEnv(c)
        try:
            kw=dict(n_steps=32,batch_size=32,n_epochs=1,device='cpu')
            a=PPO('MlpPolicy',old,seed=1,**kw);b=PPO('MlpPolicy',self.env,seed=2,**kw)
            _,migration=assert_transfer_interface(old.specification.interface(c),self.cfg,allow_lowpass_change=True)
            value=b.policy.value_net.weight.detach().clone()
            transfer_policy(a.policy,b.policy,actor_only=True,reset_log_std=None)
            obs,_=old.reset(seed=3)
            np.testing.assert_allclose(a.predict(obs,deterministic=True)[0],b.predict(obs,deterministic=True)[0],atol=1e-7)
            torch.testing.assert_close(a.policy.log_std,b.policy.log_std)
            torch.testing.assert_close(value,b.policy.value_net.weight)
            self.assertTrue(migration['control_changed'])
        finally:old.close()
    def test_success_quality_and_new_selection_serialize(self):
        import torch
        from stable_baselines3 import PPO
        from stackchan_rl.evaluation import evaluate_agent
        import json
        torch.set_num_threads(1)
        agent=PPO('MlpPolicy',self.env,n_steps=32,batch_size=32,n_epochs=1,device='cpu')
        result=evaluate_agent(agent,self.cfg,1,917,command=.02)
        self.assertEqual(result['selection_version'],4)
        self.assertEqual(len(result['selection_key']),6)
        self.assertTrue(result['physics_executed'])
        json.dumps(result,allow_nan=False)

if __name__=='__main__':unittest.main()
