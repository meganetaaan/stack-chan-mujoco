#!/usr/bin/env python3
"""Development execution of the frozen maneuver schedule; not held-out acceptance."""
import argparse
import gzip
import json
from pathlib import Path
import sys
import numpy as np
from maneuver_reference import CommandReference
from stackchan_rl.maneuver_env import ManeuverEnv
from stackchan_rl.maneuver_protocol import validate, score_motion
from stackchan_rl.residual import sha


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cad-design', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--duration', type=float, default=205.)
    p.add_argument('--seed', type=int, default=310201)
    p.add_argument('--randomize', action='store_true')
    p.add_argument('--yaw-feedback', action='store_true')
    a = p.parse_args()
    protocol = json.loads(Path('configs/maneuver/acceptance_v1.json').read_text())
    end = validate(protocol)[-1]
    if a.out.exists() or not np.isfinite(a.duration) or not 0<a.duration<=end:
        p.error('new output directory and duration in (0,205] required')
    if not np.isclose(a.duration/.02, round(a.duration/.02), atol=1e-9, rtol=0):
        p.error('duration must coincide with a 20 ms control sample')
    if a.seed in protocol['fixed_seeds']+protocol['randomized_seeds']:
        p.error('reserved acceptance seed; use a development seed')
    a.out.mkdir(parents=True)
    sys.path.insert(0, str(a.cad_design.resolve()/'src'))
    from tab5_biped.core import smooth
    from tab5_biped.planner import Planner, pose, static_torques
    planner = CommandReference(Planner(steps=1), pose, smooth, protocol)
    reference = []
    source_paths = ['probe_maneuvers.py', 'maneuver_reference.py', 'stackchan_rl/maneuver_env.py']
    report = {'scope': 'development maneuver trial; not reserved-seed acceptance',
              'seed': a.seed, 'randomized': a.randomize, 'requested_duration_s': a.duration,
              'yaw_feedback': a.yaw_feedback,
              'source_sha256': {name: sha(name) for name in source_paths},
              'planning_failure': None, 'physics_executed': False}
    for t in np.arange(0, a.duration+.01, .02):
        try:
            s = planner.sample(float(t))
            tau, _ = static_torques(s.q, s.base, s.support)
            reference.append({'time_s': float(t), 'q': s.q.tolist(), 'base': s.base.tolist(),
                              'support': s.support.tolist(), 'quasistatic_torque_Nm': tau.tolist(), 'phase': s.phase})
        except ValueError as exc:
            report['planning_failure'] = {'time_s': float(t), 'reason': str(exc)}
            break
    if report['planning_failure']:
        (a.out/'report.json').write_text(json.dumps(report, indent=2)+'\n')
        print(json.dumps(report)); return
    reference_path = a.out/'reference.json.gz'
    with gzip.open(reference_path, 'wt') as f:
        json.dump(reference, f)
    config = json.loads(Path('policies/r6_mounted_seed20260924/config.json').read_text())
    config.update(schema='r6-maneuver-v1', reference=str(reference_path.resolve()),
                  episode_s=a.duration, randomize=a.randomize)
    (a.out/'config.json').write_text(json.dumps(config, indent=2)+'\n')
    (a.out/'protocol.json').write_text(json.dumps(protocol, indent=2)+'\n')
    env = ManeuverEnv(config, protocol, record=True)
    try:
        obs, _ = env.reset(seed=a.seed, options={'randomize': a.randomize})
        def measured():
            rot = env.data.xmat[env.base].reshape(3, 3)
            return [float(env.data.time), *env.data.xpos[env.base, :2], float(np.arctan2(rot[1, 0], rot[0, 0]))]
        motion = [measured()]
        while True:
            action = np.zeros(10)
            if a.yaw_feedback:
                error = np.arctan2(np.sin(np.arctan2(obs[71], obs[72])-np.arctan2(obs[65], obs[66])),
                                   np.cos(np.arctan2(obs[71], obs[72])-np.arctan2(obs[65], obs[66])))
                turn = np.clip(obs[70]/.16 + 2.*error, -1., 1.)
                action[[1, 2]] = turn
                action[[6, 7]] = -turn
            obs, _, done, truncated, info = env.step(action)
            motion.append(measured())
            if done or truncated:
                break
        env.save_trajectory(a.out/'states.npz')
        motion = np.array(motion)
        np.savez_compressed(a.out/'motion.npz', time_s=motion[:, 0], xy_m=motion[:, 1:3], yaw_rad=motion[:, 3])
        complete = abs(motion[-1, 0]-end)<1e-8
        scoring = score_motion(protocol, motion[:, 0], motion[:, 1:3], motion[:, 3], allow_partial=True)
        counts = env.tracker.segment_landings
        landing_pass = all(s['mode']=='stop' or np.all(counts[i]>=protocol['walking_evidence']['minimum_valid_landings_each_foot_per_moving_segment'])
                           for i, s in enumerate(protocol['segments']))
        report.update(physics_executed=True, **info, complete_schedule=bool(complete),
                      motion_scoring=scoring, landing_requirements_pass=bool(landing_pass),
                      development_trial_pass=bool(complete and info['failure'] is None and landing_pass and scoring['motion_pass']),
                      interface=env.fingerprint, trajectory_sha256=sha(a.out/'states.npz'),
                      motion_sha256=sha(a.out/'motion.npz'))
        (a.out/'report.json').write_text(json.dumps(report, indent=2)+'\n')
        print(json.dumps({k: report[k] for k in ('failure', 'time_s', 'complete_schedule', 'development_trial_pass')}))
    finally:
        env.close()


if __name__ == '__main__':
    main()
