#!/usr/bin/env python3
"""Render recorded MuJoCo integration states, never IK or interpolated poses."""
import argparse
import json
from pathlib import Path
import subprocess
import mujoco
import numpy as np
from stackchan_rl.residual import ResidualEnv,STATE_SPEC,sha


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--batch',type=Path,required=True)
    p.add_argument('--trial',default='trial_00')
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    if args.out.exists():p.error('use a new video path')
    folder=args.batch/args.trial
    report=json.loads((folder/'report.json').read_text());config=json.loads((args.batch/'config.json').read_text())
    if sha(folder/'states.npz')!=report['trajectory_sha256']:raise ValueError('trajectory hash mismatch')
    env=ResidualEnv(config,visuals=True)
    if json.dumps(env.fingerprint,sort_keys=True)!=json.dumps(report['interface'],sort_keys=True):
        raise ValueError('model/code fingerprint mismatch')
    env.reset(seed=report['seed'],options={'randomize':report['domain']=='randomized'})
    if env.parameters!=report['parameters']:raise ValueError('plant reconstruction mismatch')
    trace=np.load(folder/'states.npz',allow_pickle=False)
    if int(trace['state_spec'])!=int(STATE_SPEC):raise ValueError('state specification mismatch')
    states=trace['state'];times=states[:,0]
    # Terminal failures can occur between policy samples. Use the exact recorded
    # frame; frame-time quantization affects only the movie, never reported time.
    camera=mujoco.MjvCamera();camera.distance=.5;camera.azimuth=135;camera.elevation=-15
    option=mujoco.MjvOption();option.geomgroup[3]=0
    args.out.parent.mkdir(parents=True,exist_ok=True)
    cmd=['ffmpeg','-v','error','-n','-f','rawvideo','-pixel_format','rgb24','-video_size','640x480',
         '-framerate','50','-i','-','-an','-c:v','libx264','-preset','fast','-crf','22','-pix_fmt','yuv420p',str(args.out)]
    process=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    try:
        with mujoco.Renderer(env.model,height=480,width=640) as renderer:
            for state in states:
                mujoco.mj_setState(env.model,env.data,state,STATE_SPEC);mujoco.mj_forward(env.model,env.data)
                # Follow only the camera. This does not modify the robot state.
                camera.lookat[:]=env.data.xpos[env.base];camera.lookat[2]=.11
                renderer.update_scene(env.data,camera,scene_option=option)
                process.stdin.write(renderer.render().tobytes())
    finally:
        process.stdin.close();code=process.wait();env.close()
    if code:raise RuntimeError(f'ffmpeg exit {code}')
    metadata={'source':'recorded MuJoCo integration states','synthesized_robot_motion':False,
        'state_sha256':sha(folder/'states.npz'),'video_sha256':sha(args.out),'report_sha256':sha(folder/'report.json'),
        'frames':len(states),'first_time_s':float(times[0]),'last_time_s':float(times[-1]),'fps':50,
        'camera_follows_base':True,'render_script_sha256':sha(__file__)}
    args.out.with_suffix('.json').write_text(json.dumps(metadata,indent=2)+'\n')
    print(json.dumps(metadata,indent=2))


if __name__=='__main__':main()
