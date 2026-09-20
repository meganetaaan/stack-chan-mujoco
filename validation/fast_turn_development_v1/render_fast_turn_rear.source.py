#!/usr/bin/env python3
"""Render recorded qpos states; no synthesized robot trajectory or control."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import mujoco
import numpy as np
from stackchan_rl.residual import runtime_xml


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--design',type=Path,required=True);p.add_argument('--trial',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    if a.out.exists() or a.out.with_suffix('.json').exists():p.error('new output required')
    sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
    report=json.loads((a.trial/'report.json').read_text())
    scene=a.design/'models/scene.xml'
    if sha(scene) not in report['source_sha256'].values():raise ValueError('trial model hash mismatch')
    with np.load(a.trial/'states.npz',allow_pickle=False) as s:time=s['time'];qpos=s['qpos']
    if not np.allclose(np.diff(time),.02,atol=1e-8):raise ValueError('50 Hz complete trace required')
    model=mujoco.MjModel.from_xml_string(runtime_xml(scene,visuals=True));data=mujoco.MjData(model)
    camera=mujoco.MjvCamera();camera.distance=.55;camera.azimuth=35;camera.elevation=-18
    camera.lookat[:]=[0,0,.11]
    option=mujoco.MjvOption();option.geomgroup[3]=0;option.sitegroup[:]=0
    a.out.parent.mkdir(parents=True,exist_ok=True)
    command=['ffmpeg','-v','error','-n','-f','rawvideo','-pixel_format','rgb24','-video_size','640x480',
             '-framerate','50','-i','-','-an','-c:v','libx264','-preset','fast','-crf','22','-pix_fmt','yuv420p',str(a.out)]
    process=subprocess.Popen(command,stdin=subprocess.PIPE)
    try:
        with mujoco.Renderer(model,height=480,width=640) as renderer:
            for q in qpos:
                data.qpos[:]=q;mujoco.mj_forward(model,data)
                renderer.update_scene(data,camera,scene_option=option)
                process.stdin.write(renderer.render().tobytes())
    finally:
        process.stdin.close();code=process.wait()
    if code:raise RuntimeError('ffmpeg failed')
    meta={'scope':__doc__,'frames':len(time),'fps':50,'first_time_s':float(time[0]),'last_time_s':float(time[-1]),
          'source_sha256':{str(f):sha(f) for f in [Path(__file__),scene,a.trial/'states.npz',a.trial/'report.json',a.out]}}
    a.out.with_suffix('.json').write_text(json.dumps(meta,indent=2)+'\n');print(json.dumps(meta))


if __name__=='__main__':main()
