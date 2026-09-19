import copy
import gzip
import json
from pathlib import Path
import tempfile
import unittest
import mujoco
import numpy as np
from stackchan_rl.maneuver_env import ManeuverEnv, CommandWalkTracker
from stackchan_rl.residual_heading import HeadingResidualEnv
from stackchan_rl.walk_events import WalkEventTracker
from stackchan_rl.config import DEFAULT


class CommandTrackerTests(unittest.TestCase):
    def test_stop_only_exempts_no_step_timer(self):
        tracker = CommandWalkTracker(WalkEventTracker(.001, DEFAULT['env']), 2)
        args = ([True, True], [0., 0.], [[0., .02], [0., -.02]], 0., True)
        for _ in range(4000):
            result = tracker.update(*args)
        self.assertEqual(result['no_step_elapsed_s'], 0.)
        np.testing.assert_array_equal(tracker.counts, [0, 0])
        tracker.moving = True
        tracker.segment_index = 1
        for _ in range(1500):
            result = tracker.update(*args)
        self.assertGreater(result['no_step_elapsed_s'], 1.)
        np.testing.assert_array_equal(tracker.segment_landings, np.zeros((2, 2)))


class ManeuverEnvironmentTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.protocol = json.loads(Path('configs/maneuver/acceptance_v1.json').read_text())
        self.config = json.loads(Path('policies/r6_mounted_seed20260924/config.json').read_text())
        with gzip.open(self.config['reference'], 'rt') as source:
            initial = json.load(source)[0]
        reference = []
        for t in np.arange(0, 4.001, .02):
            sample = copy.deepcopy(initial)
            sample['time_s'] = float(t)
            reference.append(sample)
        path = Path(self.directory.name)/'stand.json.gz'
        with gzip.open(path, 'wt') as output:
            json.dump(reference, output)
        self.config.update(schema='r6-maneuver-v1', reference=str(path), episode_s=4., randomize=False)

    def env(self):
        env = ManeuverEnv(self.config, self.protocol, record=True)
        self.addCleanup(env.close)
        return env

    def test_standing_executes_without_false_walking_failure_and_records_commands(self):
        env = self.env()
        obs, _ = env.reset(seed=310099)
        self.assertEqual(obs.shape, (73,))
        self.assertEqual(obs[59], 0.)
        while True:
            _, _, done, truncated, info = env.step(np.zeros(10))
            if done or truncated:
                break
        self.assertIsNone(info['failure'])
        self.assertAlmostEqual(info['time_s'], 4., places=8)
        self.assertEqual(info['valid_landings'], [0, 0])
        path = Path(self.directory.name)/'states.npz'
        env.save_trajectory(path)
        with np.load(path, allow_pickle=False) as saved:
            self.assertEqual(saved['executed_commands'].shape, (200, 4))
            np.testing.assert_array_equal(saved['executed_commands'][:, 2:], 0.)
            self.assertEqual(saved['landing_events'].shape, (0, 3))
        # New command is observable at the exact boundary, but was not applied
        # retroactively to the previous [3.98,4.00] control interval.
        self.assertAlmostEqual(env.observations[-1][59], .1, places=7)

    def test_zero_action_plant_and_noise_match_parent_before_stepping_guard(self):
        env = self.env()
        parent = HeadingResidualEnv({**self.config, 'schema': 'r6-residual-heading-v2', 'command_m_s': .1})
        self.addCleanup(parent.close)
        env.reset(seed=310099)
        parent.reset(seed=310099)
        for _ in range(70):
            env.step(np.zeros(10))
            parent.step(np.zeros(10))
        np.testing.assert_array_equal(env.data.qpos, parent.data.qpos)
        np.testing.assert_array_equal(env.data.qvel, parent.data.qvel)

    def test_stop_does_not_exempt_joint_limit_or_tilt(self):
        env = self.env()
        env.reset(seed=310099)
        env.data.qpos[env.qadr[0]] = env.limits[0, 1]+.001
        mujoco.mj_forward(env.model, env.data)
        self.assertEqual(env._check_physics(), 'joint_limit')
        env.reset(seed=310099)
        env.data.qpos[3:7] = [np.cos(.5), np.sin(.5), 0., 0.]
        mujoco.mj_forward(env.model, env.data)
        self.assertEqual(env._check_physics(), 'fall')

    def test_backward_and_yaw_commands_at_boundaries(self):
        env = self.env()
        self.assertAlmostEqual(env.command(18.)[1][0], -.05)
        self.assertGreater(env.command(32.)[1][1], 0.)
        self.assertLess(env.command(46.)[1][1], 0.)
        with self.assertRaises(ValueError):
            env.command(206.)


if __name__ == '__main__':
    unittest.main()
