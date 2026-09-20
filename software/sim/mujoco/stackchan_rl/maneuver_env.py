"""Command-aware ten-axis development environment with unchanged plant checks.

The joint reference must be supplied by a controller/reference generator. This
class does not itself demonstrate maneuverability or acceptance. It retains the
heading environment's explicitly simulated external pose estimate.
"""
import copy
from collections import deque
import gymnasium as gym
import numpy as np
from .maneuver_protocol import validate
from .residual import ROOT, sha
from .residual_heading import HeadingResidualEnv


class CommandWalkTracker:
    """Keep physical contact qualification; require stepping only while moving."""
    def __init__(self, tracker, segment_count):
        self.tracker = tracker
        self.segment_index = 0
        self.moving = False
        self.segment_landings = np.zeros((segment_count, 2), dtype=int)
        self.landing_events = []

    def __getattr__(self, name):
        return getattr(self.tracker, name)

    def update(self, contacts, heights, feet_xy, base_forward, active):
        result = self.tracker.update(contacts, heights, feet_xy, base_forward, self.moving)
        for foot in result['valid_landing_feet']:
            self.segment_landings[self.segment_index, foot] += 1
            self.landing_events.append({'time_s': self.tracker.t,
                                        'segment_index': self.segment_index,
                                        'foot': int(foot)})
        return result


class ManeuverEnv(HeadingResidualEnv):
    """Body vx/yaw-rate commands; stop exempts only the no-step requirement."""
    def __init__(self, config, protocol, **kwargs):
        if config['schema'] != 'r6-maneuver-v1':
            raise ValueError('requires maneuver-v1 configuration')
        self.protocol = copy.deepcopy(protocol)
        self.boundaries = validate(self.protocol)
        self.commands = np.array([[s['vx_m_s'], s['yaw_rate_rad_s']]
                                  for s in self.protocol['segments']])
        self.heading_targets = np.r_[0., np.cumsum(self.commands[:, 1] * np.diff(self.boundaries))]
        if not 0 < config['episode_s'] <= self.boundaries[-1]:
            raise ValueError('episode must fit the command schedule')
        dt = config['policy_dt_s']
        if not np.allclose(self.boundaries / dt, np.round(self.boundaries / dt), atol=1e-8, rtol=0):
            raise ValueError('command boundaries must coincide with control samples')
        base_config = copy.deepcopy(config)
        base_config.update(schema='r6-residual-heading-v2', command_m_s=.1)
        super().__init__(base_config, **kwargs)
        self.observation_space = gym.spaces.Box(-np.inf, np.inf, (73,), np.float32)
        self.fingerprint['schema'] = config['schema']
        self.fingerprint['source_sha256']['stackchan_rl/maneuver_env.py'] = sha(ROOT/'stackchan_rl/maneuver_env.py')
        self.fingerprint['source_sha256']['stackchan_rl/maneuver_protocol.py'] = sha(ROOT/'stackchan_rl/maneuver_protocol.py')
        self.fingerprint['protocol'] = self.protocol
        self.fingerprint['observation_fields'] += [('command_yaw_rate', 1), ('target_heading_sin_cos', 2)]
        self.fingerprint['command_semantics'] = 'obs[59]=body vx; obs[70]=world vertical yaw rate'
        self.fingerprint['control_parameters']['command_m_s'] = 'scheduled; see protocol'
        self.fingerprint['walking_requirement'] = 'qualified landings during nonzero commands; stop exempt'

    def command(self, time_s):
        # Clamp only accumulated timestep roundoff, never an out-of-schedule time.
        if not np.isfinite(time_s) or time_s < -1e-9 or time_s > self.boundaries[-1]+1e-8:
            raise ValueError('time outside command schedule')
        t = float(np.clip(time_s, 0., self.boundaries[-1]))
        index = min(np.searchsorted(self.boundaries, t+1e-9, side='right')-1, len(self.commands)-1)
        heading = self.heading_targets[index] + self.commands[index, 1]*(t-self.boundaries[index])
        return int(index), self.commands[index].copy(), float(heading)

    def _observation(self):
        obs = super()._observation()
        _, command, heading = self.command(self.data.time)
        obs[59] = command[0]
        return np.r_[obs, command[1], np.sin(heading), np.cos(heading)].astype(np.float32)

    def reset(self, **kwargs):
        obs, info = super().reset(**kwargs)
        self.tracker = CommandWalkTracker(self.tracker, len(self.commands))
        self.motion_window = deque(maxlen=max(1, round(.5/self.dt)))
        self.executed_commands = []
        return obs, {**info, 'command': self.command(0.)[1].tolist()}

    def step(self, action):
        index, command, _ = self.command(self.data.time)
        self.tracker.segment_index = index
        self.tracker.moving = bool(np.any(command != 0.))
        self.cfg['command_m_s'] = float(command[0])
        before_xy = self.data.xpos[self.base, :2].copy()
        rot = self.data.xmat[self.base].reshape(3, 3)
        before_yaw = np.arctan2(rot[1, 0], rot[0, 0])
        before_time = self.data.time
        previous_action = self.previous_action.copy()
        # Parent advances every physics substep and checks collisions, limits,
        # tilt, invalid physics and actuator protection. No failure is cleared.
        obs, _, terminated, truncated, info = super().step(action)
        rot = self.data.xmat[self.base].reshape(3, 3)
        yaw = np.arctan2(rot[1, 0], rot[0, 0])
        dyaw = np.arctan2(np.sin(yaw-before_yaw), np.cos(yaw-before_yaw))
        elapsed = self.data.time-before_time
        motion = np.zeros(3)
        if elapsed > 0:
            velocity = (self.data.xpos[self.base, :2]-before_xy)/elapsed
            heading = before_yaw+dyaw/2
            motion[:] = [np.cos(heading)*velocity[0]+np.sin(heading)*velocity[1],
                         -np.sin(heading)*velocity[0]+np.cos(heading)*velocity[1], dyaw/elapsed]
        self.motion_window.append(motion)
        mean = np.mean(self.motion_window, axis=0)
        a = self.previous_action
        reward = float(np.exp(-((mean[0]-command[0])/.04)**2-((mean[2]-command[1])/.12)**2))
        reward -= .2*min((mean[1]/.04)**2, 10.) + .05*np.mean(a*a) + .02*np.mean((a-previous_action)**2)
        if self.failure:
            reward -= 10.
        self.executed_commands.append([float(before_time), index, *command.tolist()])
        info.update(segment_index=index, command=command.tolist(),
                    measured_body_vx_vy_yaw_rate=motion.tolist(),
                    segment_valid_landings=self.tracker.segment_landings.tolist())
        return obs, float(reward), terminated, truncated, info

    def save_trajectory(self, path):
        super().save_trajectory(path)
        # Keep the original full integration state and add actual command/event
        # history required to audit which segment was active at each step.
        with np.load(path, allow_pickle=False) as source:
            arrays = {name: source[name] for name in source.files}
        arrays['executed_commands'] = np.asarray(self.executed_commands)
        arrays['segment_valid_landings'] = self.tracker.segment_landings
        arrays['landing_events'] = np.array([[x['time_s'], x['segment_index'], x['foot']]
                                            for x in self.tracker.landing_events], dtype=float).reshape(-1, 3)
        np.savez_compressed(path, **arrays)
