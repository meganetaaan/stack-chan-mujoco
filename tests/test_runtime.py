"""Real MuJoCo/Gymnasium/SB3 tests, explicitly SKIPPED when unavailable.

No mock physics engine is substituted. These are software tests, not a claim that
64 PPO steps train a useful controller. GUI/WSLg requires the separate play test.
"""
from __future__ import annotations
import importlib.util
from pathlib import Path
import tempfile
import unittest
import numpy as np
from stackchan_rl.config import ROOT, load_config

AVAILABLE = all(importlib.util.find_spec(n) is not None for n in ("mujoco", "gymnasium", "stable_baselines3"))


@unittest.skipUnless(AVAILABLE, "MuJoCo / Gymnasium / SB3 missing: real runtime NOT EXECUTED")
class RuntimeTests(unittest.TestCase):
    def setUp(self):
        from stackchan_rl.env import StackChanEnv
        self.cfg = load_config(ROOT / "configs/stand.json")
        self.env = StackChanEnv(self.cfg)

    def tearDown(self):
        self.env.close()

    def test_actual_A_compiles_and_steps(self):
        o, _ = self.env.reset(seed=31, options={"no_noise": True})
        self.assertEqual(o.shape, (61,))
        self.assertEqual((self.env.model.nq, self.env.model.nv, self.env.model.nu), (17,16,10))
        self.assertAlmostEqual(float(self.env.model.body_mass.sum()), self.env.specification.mass, places=8)
        o, r, t, tr, i = self.env.step(np.zeros(10))
        self.assertTrue(np.isfinite(o).all())
        self.assertTrue(np.isfinite(r))
        self.assertGreater(self.env.data.time, 0)
        self.assertFalse(t, i["failure_reason"])
        self.assertFalse(tr)

    def test_SB3_env_contract(self):
        from stable_baselines3.common.env_checker import check_env
        check_env(self.env, warn=True, skip_render_check=True)

    def test_seeded_reset_and_step(self):
        o1, i1 = self.env.reset(seed=39)
        a = np.linspace(-.1, .1, 10).astype(np.float32)
        step1 = self.env.step(a)
        o2, i2 = self.env.reset(seed=39)
        step2 = self.env.step(a)
        np.testing.assert_allclose(o1, o2, atol=1e-7)
        np.testing.assert_allclose(step1[0], step2[0], atol=1e-7)
        self.assertAlmostEqual(step1[1], step2[1], places=8)
        self.assertEqual(step1[2:4], step2[2:4])

    def test_time_limit_is_truncation(self):
        from stackchan_rl.env import StackChanEnv
        self.cfg["env"]["episode_seconds"] = .02
        short = StackChanEnv(self.cfg)
        try:
            short.reset(seed=4, options={"no_noise": True})
            _, _, term, trunc, info = short.step(np.zeros(10))
            self.assertFalse(term, info["failure_reason"])
            self.assertTrue(trunc)
            with self.assertRaises(RuntimeError):
                short.step(np.zeros(10))
        finally:
            short.close()

    def test_fall_is_termination(self):
        import mujoco
        from stackchan_rl.math_utils import euler_quat
        self.env.reset(seed=5, options={"no_noise": True})
        r = self.env.root_qadr
        self.env.data.qpos[r+3:r+7] = euler_quat(0, np.deg2rad(60), 0)
        mujoco.mj_forward(self.env.model, self.env.data)
        _, reward, term, trunc, info = self.env.step(np.zeros(10))
        self.assertTrue(term)
        self.assertFalse(trunc)
        self.assertFalse(info["is_success"])
        self.assertEqual(reward, -self.cfg["reward"]["termination"])

    def test_torque_interface_and_no_root_assist(self):
        self.env.reset(seed=6, options={"no_noise": True})
        _, _, _, _, _ = self.env.step(np.full(10, .5))
        self.assertTrue(np.all(np.abs(self.env.data.ctrl[self.env.aidx]) <= self.env.bank.cap + 1e-10))
        self.assertEqual(self.env.model.neq, 0)
        np.testing.assert_allclose(self.env.data.xfrc_applied, 0)
        np.testing.assert_allclose(self.env.data.qfrc_applied, 0)
        np.testing.assert_allclose(self.env.model.body_gravcomp, 0)

    def test_domain_randomization_is_not_cumulative(self):
        self.env.reset(seed=18, options={"domain_randomization": True})
        one = self.env.model.body_mass.copy()
        self.env.reset(seed=18, options={"domain_randomization": True})
        np.testing.assert_allclose(one, self.env.model.body_mass)
        self.env.reset(seed=18, options={"domain_randomization": False})
        np.testing.assert_allclose(self.env._nom_mass, self.env.model.body_mass)

    def test_headless_visual_physics_agree(self):
        import mujoco
        full = mujoco.MjModel.from_xml_string(self.env.specification.runtime_xml(visuals=True))
        for field in ("body_mass", "body_inertia", "body_ipos", "body_iquat", "body_pos", "jnt_pos", "jnt_axis", "jnt_range", "actuator_ctrlrange", "dof_armature", "dof_damping", "dof_frictionloss"):
            np.testing.assert_allclose(getattr(full, field), getattr(self.env.model, field), err_msg=field)

    def test_real_PPO_update_save_and_reload(self):
        import torch
        from stable_baselines3 import PPO
        from stackchan_rl.checkpoints import save_bundle, bundle_info, assert_interface
        torch.set_num_threads(1)
        agent = PPO("MlpPolicy", self.env, n_steps=32, batch_size=32, n_epochs=1,
                    policy_kwargs={"net_arch": [32,32]}, device="cpu", seed=91, verbose=0)
        before = {k:v.detach().clone() for k,v in agent.policy.state_dict().items()}
        agent.learn(total_timesteps=64)
        self.assertEqual(agent.num_timesteps, 64)
        self.assertTrue(any(not torch.equal(v, before[k]) for k,v in agent.policy.state_dict().items()))
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/"checkpoint"
            save_bundle(agent, path, self.cfg, self.env.specification.interface(self.cfg), {})
            cp, cfg, interface, meta = bundle_info(path)
            assert_interface(interface, cfg)
            clone = PPO.load(str(cp/"model.zip"), device="cpu")
            obs, _ = self.env.reset(seed=99)
            a1,_ = agent.predict(obs, deterministic=True)
            a2,_ = clone.predict(obs, deterministic=True)
            np.testing.assert_allclose(a1, a2, atol=1e-7)


if __name__ == "__main__":
    unittest.main(verbosity=2)
