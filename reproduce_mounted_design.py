#!/usr/bin/env python3
"""Regenerate mounted-battery CAD and MJCF from tracked sources in a fresh folder.

Run with the documented CadQuery Python environment. No existing output is reused.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();out=a.out.resolve()
    if out.exists():p.error('new output directory required')
    root=Path(__file__).resolve().parent
    out.mkdir(parents=True)
    commands=[
        ['build_design.py','--out',str(out/'rear_bridge'),'--hip-half-spacing-mm','22',
         '--battery-layout','design/battery_layouts/internal_lower_envelope.json',
         '--underside-cutouts','design/leg_relief/underside_cutouts.json',
         '--leg-clearance-relief','--boot-collar-relief','--rear-gimbal-bridge'],
        ['add_gimbal_collisions.py','--design',str(out/'rear_bridge'),'--out',str(out/'gimbal_collisions')],
        ['add_base_reservation_collisions.py','--design',str(out/'gimbal_collisions'),'--out',str(out/'base_collisions')],
        ['build_battery_mount.py','--design',str(out/'base_collisions'),'--out',str(out/'mount')],
        ['integrate_battery_mount.py','--design',str(out/'base_collisions'),'--mount',str(out/'mount'),'--out',str(out/'model')],
    ]
    manifest={'scope':'Fresh CAD and model generation, no training or walking evaluation','complete':False,'commands':commands,'completed':0}
    target=out/'regeneration.json'
    target.write_text(json.dumps(manifest,indent=2)+'\n')
    for i,command in enumerate(commands):
        print(f'{i+1}/{len(commands)}: {command[0]}',flush=True)
        with (out/f'step_{i+1}.log').open('w') as log:
            subprocess.run([sys.executable,*command],cwd=root,stdout=log,stderr=subprocess.STDOUT,check=True)
        manifest['completed']=i+1;target.write_text(json.dumps(manifest,indent=2)+'\n')
    manifest['complete']=True;target.write_text(json.dumps(manifest,indent=2)+'\n')


if __name__=='__main__':main()
