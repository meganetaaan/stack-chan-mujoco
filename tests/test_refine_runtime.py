"""Actual MuJoCo/SB3 integration tests. Skipped, not mocked, when unavailable."""
from __future__ import annotations
from copy import deepcopy
import importlib.util
from pathlib import Path
import tempfile
import unittest
import numpy as np
from stackchan_rl.config import ROOT,load_config

AVAILABLE=all(importlib.util.find_spec(n) is not None for n in ('mujoco','gymnasium','stable_baselines3'))

@unittest.skipUnless(AVAILABLE, 'MuJoCo/Gymnasium/SB3 missing: v3 runtime NOT EXECUTED')
class RefineRuntimeTests(unittest.TestCase):
    def setUp(self):
        from stackchan_rl.env import StackChanEnv
        self.c=load_config(ROOT/'configs/refine_smoke.json')
        self.c['env']['measurement_start_s']=0.
        self.env=StackChanEnv(self.c)
    def tearDown(self):self.env.close()
    def test_SB3_contract(self):
        from stable_baselines3.common.env_checker import check_env
        check_env(self.env,warn=True,skip_render_check=True)
    def test_substep_sample_count_and_pitch_rate(self):
        self.env.reset(seed=4,options={'no_noise':True})
        self.env.step(np.zeros(10,dtype=np.float32))
        q=self.env._quality_latest
        self.assertEqual(q['quality_sample_count'],self.env.substeps)
        self.assertTrue(np.isfinite(q['pitch_rate_sq']))
        self.assertTrue(np.isfinite(q['impact_load_cost']))
    def test_telemetry_does_not_change_physics_or_legacy_rewards(self):
        from stackchan_rl.env import StackChanEnv
        c=load_config(ROOT/'configs/walk_smoke.json')
        a=StackChanEnv(c);c['env']['gait_quality_metrics']=True;b=StackChanEnv(c)
        try:
            oa,_=a.reset(seed=5,options={'no_noise':True});ob,_=b.reset(seed=5,options={'no_noise':True})
            np.testing.assert_array_equal(oa,ob)
            for _ in range(5):
                oa,ra,ta,tra,_=a.step(np.zeros(10));ob,rb,tb,trb,_=b.step(np.zeros(10))
                np.testing.assert_allclose(a.data.qpos,b.data.qpos,atol=1e-12,rtol=0)
                np.testing.assert_allclose(a.data.qvel,b.data.qvel,atol=1e-12,rtol=0)
                np.testing.assert_array_equal(oa,ob);self.assertEqual(ra,rb)
                self.assertEqual((ta,tra),(tb,trb))
                if ta or tra:break
        finally:a.close();b.close()
    def test_quality_csv_schema_fixed_across_episode(self):
        self.env.reset(seed=3);keys=set(self.env.trajectory_row())
        self.assertIn('substep_pitch_rate_rms_rad_s',keys)
        for _ in range(self.env.max_steps):
            _,_,term,trunc,info=self.env.step(np.zeros(10))
            self.assertEqual(keys,set(self.env.trajectory_row()))
            if term or trunc:
                s=info['episode_summary'];self.assertIn('quality_checks',s)
                self.assertIn('pitch_rate_rms_rad_s',s);self.assertIn('failed_checks',s);break
        else:self.fail('No episode completion')
    def test_actual_SB3_transfer_preserves_mean_AND_exploration(self):
        from stable_baselines3 import PPO
        from stackchan_rl.transfer import transfer_policy
        import torch
        torch.set_num_threads(1)
        kw=dict(policy_kwargs={'net_arch':{'pi':[64,64],'vf':[64,64]}},n_steps=32,batch_size=32,n_epochs=1,device='cpu')
        a=PPO('MlpPolicy',self.env,seed=10,**kw);b=PPO('MlpPolicy',self.env,seed=20,**kw)
        with torch.no_grad():a.policy.log_std.copy_(torch.linspace(-2.,-.5,10))
        obs,_=self.env.reset(seed=7)
        v=b.policy.value_net.weight.detach().clone()
        transfer_policy(a.policy,b.policy,actor_only=True,reset_log_std=None)
        np.testing.assert_allclose(a.predict(obs,deterministic=True)[0],b.predict(obs,deterministic=True)[0],atol=1e-6)
        torch.testing.assert_close(a.policy.log_std,b.policy.log_std)
        torch.testing.assert_close(v,b.policy.value_net.weight)
    def test_short_PPO_save_load_evaluate_and_selection_v3(self):
        from stable_baselines3 import PPO
        from stackchan_rl.checkpoints import save_bundle,bundle_info,assert_interface
        from stackchan_rl.evaluation import evaluate_agent
        import torch
        torch.set_num_threads(1)
        agent=PPO('MlpPolicy',self.env,n_steps=32,batch_size=32,n_epochs=1,device='cpu',seed=11)
        agent.learn(64)
        with tempfile.TemporaryDirectory() as d:
            save_bundle(agent,Path(d)/'bundle',self.c,self.env.specification.interface(self.c))
            p,c,iface,_=bundle_info(Path(d)/'bundle');assert_interface(iface,c)
            loaded=PPO.load(str(p/'model.zip'),device='cpu')
            callbacks=[]
            r=evaluate_agent(loaded,c,1,12,command=.02,trajectory_dir=Path(d)/'csv',on_episode=callbacks.append)
            self.assertEqual(len(r['selection_key']),6);self.assertTrue(r['physics_executed'])
            self.assertEqual(len(callbacks),1);self.assertEqual(r['quality_measured_episodes'],1)
    def test_reset_clears_all_quality_history(self):
        self.env.reset(seed=1,options={'no_noise':True});self.env.step(np.zeros(10))
        self.assertGreater(self.env.quality.n,0)
        self.env.reset(seed=1,options={'no_noise':True});self.assertEqual(self.env.quality.n,0)
        self.assertIsNone(self.env.quality.last_landing)
    def test_object_velocity_axis_matches_existing_jacobian_measurement(self):
        import mujoco
        self.env.reset(seed=1,options={'no_noise':True})
        from stackchan_rl.math_utils import euler_quat
        self.env.data.qpos[self.env.root_qadr+3:self.env.root_qadr+7]=euler_quat(.1,.2,.3)
        self.env.data.qvel[self.env.root_vadr+3:self.env.root_vadr+6]=[.2,.3,.4]
        mujoco.mj_forward(self.env.model,self.env.data)
        s=self.env._snapshot();v=np.zeros(6)
        mujoco.mj_objectVelocity(self.env.model,self.env.data,mujoco.mjtObj.mjOBJ_BODY,self.env.base_id,v,0)
        R=self.env.data.xmat[self.env.base_id].reshape(3,3)
        np.testing.assert_allclose(R.T@v[:3],s['gyro'],atol=1e-12)
