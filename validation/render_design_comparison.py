#!/usr/bin/env python3
"""Render two actual MuJoCo visual models in the same nominal pose/camera.

Headless Linux: MUJOCO_GL=egl .venv-dynamics/bin/python ...
PNG encoding uses the standard library; collision proxies are hidden visually.
"""
import argparse
from pathlib import Path
import struct
import zlib
import mujoco
import numpy as np


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline', required=True, type=Path)
    p.add_argument('--candidate', required=True, type=Path)
    p.add_argument('--out', required=True, type=Path)
    args = p.parse_args()
    images = []
    for folder in [args.baseline,args.candidate]:
        model = mujoco.MjModel.from_xml_path(str((folder/'models/scene.xml').resolve()))
        data = mujoco.MjData(model)
        if model.nkey:
            mujoco.mj_resetDataKeyframe(model,data,0)
        mujoco.mj_forward(model,data)
        camera = mujoco.MjvCamera()
        camera.lookat[:] = [0,0,.11]
        camera.distance = .46
        camera.azimuth = 215
        camera.elevation = -15
        option = mujoco.MjvOption()
        option.geomgroup[3] = 0
        with mujoco.Renderer(model,height=600,width=600) as renderer:
            renderer.update_scene(data,camera,scene_option=option)
            images.append(renderer.render().copy())
    pixels = np.concatenate(images,axis=1)
    height,width,_ = pixels.shape
    raw = b''.join(b'\0'+row.tobytes() for row in pixels)

    def chunk(kind,data):
        return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)

    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_bytes(b'\x89PNG\r\n\x1a\n'+
        chunk(b'IHDR',struct.pack('>2I5B',width,height,8,2,0,0,0))+
        chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b''))


if __name__ == '__main__':
    main()
