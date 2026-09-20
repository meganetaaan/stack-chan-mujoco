#!/usr/bin/env python3
"""Render verified recorded maneuver integration states without inventing motion."""
import argparse
import json
from pathlib import Path
import subprocess
import mujoco
import numpy as np
from stackchan_rl.maneuver_env import ManeuverEnv
from stackchan_rl.residual import STATE_SPEC, sha


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--trial', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    if args.out.exists() or args.out.with_suffix('.json').exists():
        p.error('use a new video and metadata path')
    report = json.loads((args.trial/'report.json').read_text())
    config = json.loads((args.trial/'config.json').read_text())
    config['reference'] = str((args.trial/'reference.json.gz').resolve())
    protocol = json.loads((args.trial/'protocol.json').read_text())
    state_path = args.trial/'states.npz'
    if sha(state_path) != report['trajectory_sha256']:
        raise ValueError('trajectory hash mismatch')
    env = ManeuverEnv(config, protocol, visuals=True)
    try:
        if env.fingerprint != report['interface']:
            # JSON converts tuple-based observation field definitions to lists.
            if json.dumps(env.fingerprint, sort_keys=True) != json.dumps(report['interface'], sort_keys=True):
                raise ValueError('model/code/protocol fingerprint mismatch')
        env.reset(seed=report['seed'], options={'randomize': report['randomized']})
        if env.parameters != report['parameters']:
            raise ValueError('plant reconstruction mismatch')
        with np.load(state_path, allow_pickle=False) as trace:
            if int(trace['state_spec']) != int(STATE_SPEC):
                raise ValueError('state specification mismatch')
            states = trace['state']
            commands = trace['executed_commands']
            if json.loads(str(trace['fingerprint_json'])) != report['interface']:
                raise ValueError('recorded interface mismatch')
        if not np.isfinite(states).all() or np.any(np.diff(states[:, 0]) <= 0):
            raise ValueError('invalid recorded states')
        if len(commands) != len(states)-1 or not np.allclose(commands[:, 0], states[:-1, 0], atol=1e-10, rtol=0):
            raise ValueError('command/state timeline mismatch')
        for time, index, vx, yaw_rate in commands:
            expected_index, expected, _ = env.command(time)
            if index != expected_index or not np.array_equal([vx, yaw_rate], expected):
                raise ValueError('recorded command differs from protocol')
        camera = mujoco.MjvCamera()
        camera.distance = .5
        camera.azimuth = 135
        camera.elevation = -15
        option = mujoco.MjvOption()
        option.geomgroup[3] = 0
        args.out.parent.mkdir(parents=True, exist_ok=True)
        cmd = ['ffmpeg', '-v', 'error', '-n', '-f', 'rawvideo', '-pixel_format', 'rgb24',
               '-video_size', '640x480', '-framerate', '50', '-i', '-', '-an',
               '-c:v', 'libx264', '-preset', 'fast', '-crf', '22', '-pix_fmt', 'yuv420p', str(args.out)]
        process = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        try:
            with mujoco.Renderer(env.model, height=480, width=640) as renderer:
                for state in states:
                    mujoco.mj_setState(env.model, env.data, state, STATE_SPEC)
                    mujoco.mj_forward(env.model, env.data)
                    camera.lookat[:] = env.data.xpos[env.base]
                    camera.lookat[2] = .11
                    renderer.update_scene(env.data, camera, scene_option=option)
                    process.stdin.write(renderer.render().tobytes())
        finally:
            process.stdin.close()
            code = process.wait()
        if code:
            raise RuntimeError(f'ffmpeg exit {code}')
        metadata = {'source': 'recorded MuJoCo integration states', 'synthesized_robot_motion': False,
                    'state_sha256': sha(state_path), 'video_sha256': sha(args.out),
                    'report_sha256': sha(args.trial/'report.json'), 'render_script_sha256': sha(__file__),
                    'frames': len(states), 'first_time_s': float(states[0, 0]),
                    'last_time_s': float(states[-1, 0]), 'fps': 50, 'camera_follows_base': True,
                    'complete_schedule': report['complete_schedule']}
        args.out.with_suffix('.json').write_text(json.dumps(metadata, indent=2)+'\n')
        print(json.dumps(metadata, indent=2))
    finally:
        env.close()


if __name__ == '__main__':
    main()
