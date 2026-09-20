#!/usr/bin/env python3
"""Render recorded twelve-axis integration states after checking source hashes."""
import argparse
import json
from pathlib import Path
import subprocess
import mujoco
import numpy as np
from stackchan_rl.residual import STATE_SPEC,runtime_xml,sha


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--trial',type=Path,required=True)
    p.add_argument('--design',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    if a.out.exists() or a.out.with_suffix('.json').exists():p.error('new output required')
    report=json.loads((a.trial/'report.json').read_text());state_path=a.trial/'states.npz'
    if sha(state_path)!=report['trajectory_sha256']:raise ValueError('trajectory hash mismatch')
    for name in ('models/scene.xml','robot.json'):
        original=str(Path(report['design'])/name)
        if sha(a.design/name)!=report['source_sha256'][original]:raise ValueError('model hash mismatch: '+name)
    frozen=json.loads((a.design/'FROZEN_FILES.json').read_text())
    for name,digest in frozen.items():
        if sha(a.design/name)!=digest:raise ValueError('frozen asset mismatch: '+name)
    model=mujoco.MjModel.from_xml_string(runtime_xml(a.design/'models/scene.xml',visuals=True))
    data=mujoco.MjData(model)
    with np.load(state_path,allow_pickle=False) as trace:
        if int(trace['state_spec'])!=int(STATE_SPEC):raise ValueError('state spec mismatch')
        states=trace['state']
    if states.shape[1]!=mujoco.mj_stateSize(model,STATE_SPEC) or not np.isfinite(states).all():raise ValueError('invalid state size or values')
    dt=np.diff(states[:,0])
    if len(dt)==0 or np.any(dt<=0) or not np.allclose(dt[:-1],.02,atol=1e-9,rtol=0) or dt[-1]>.020000001:raise ValueError('invalid cadence')
    if not np.isclose(states[-1,0],report['time_s'],atol=1e-9):raise ValueError('terminal time mismatch')
    camera=mujoco.MjvCamera();camera.distance=.55;camera.azimuth=135;camera.elevation=-18
    option=mujoco.MjvOption();option.geomgroup[3]=0
    a.out.parent.mkdir(parents=True,exist_ok=True)
    command=['ffmpeg','-v','error','-n','-f','rawvideo','-pixel_format','rgb24','-video_size','640x480','-framerate','50','-i','-','-an','-c:v','libx264','-preset','fast','-crf','22','-pix_fmt','yuv420p',str(a.out)]
    process=subprocess.Popen(command,stdin=subprocess.PIPE)
    try:
        with mujoco.Renderer(model,height=480,width=640) as renderer:
            for state in states:
                mujoco.mj_setState(model,data,state,STATE_SPEC);mujoco.mj_forward(model,data)
                camera.lookat[:]=data.xpos[model.body('base').id];camera.lookat[2]=.11
                renderer.update_scene(data,camera,scene_option=option)
                process.stdin.write(renderer.render().tobytes())
    finally:
        process.stdin.close();code=process.wait()
    if code:raise RuntimeError('ffmpeg failed')
    metadata={'source':'recorded MuJoCo integration states','synthesized_robot_motion':False,
              'frames':len(states),'fps':50,'first_time_s':float(states[0,0]),'last_time_s':float(states[-1,0]),
              'last_sample_interval_s':float(dt[-1]),'camera_follows_base':True,'failure':report['failure'],
              'state_sha256':sha(state_path),'video_sha256':sha(a.out),'model_sha256':sha(a.design/'models/scene.xml'),
              'report_sha256':sha(a.trial/'report.json'),'render_source_sha256':sha(__file__)}
    a.out.with_suffix('.json').write_text(json.dumps(metadata,indent=2)+'\n')
    print(json.dumps(metadata))


if __name__=='__main__':main()
