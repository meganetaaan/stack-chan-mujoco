#!/usr/bin/env python3
"""Exact CAD ankle-roll clearance along the range observed in a saved trial."""
import argparse
import itertools
import json
from pathlib import Path
import sys
import numpy as np


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--trial',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    if a.out.exists():p.error('new output required')
    source=Path('outputs/design_r6_base_collisions').resolve()
    sys.path[:0]=[str(source/'cad'),str(source/'src')]
    import cadquery as cq
    from build import build
    old={part.name:part.shape for part in build() if part.role!='visual'}
    states=np.load(a.trial/'states.npz',allow_pickle=False)['qpos']
    rows=[]
    for side,index in [('left',12),('right',18)]:
        fixed={name:old[side+'_'+name] for name in ['ankle_gimbal','ankle_roll_motor']}
        moving={name:cq.importers.importStep(str(Path('validation/fast_turn_development_v1/feet_cad_v2')/(side+'_'+name+'.step'))).val()
                for name in ['foot_yoke','boot_shell','sole_TPU']}
        worst={}
        lo,hi=float(states[:,index].min()),float(states[:,index].max())
        for angle in np.linspace(lo,hi,17):
            posed={n:s.rotate((0,0,0),(1,0,0),np.rad2deg(angle)).translate((-26,0,-10)) for n,s in moving.items()}
            for (n1,s1),(n2,s2) in itertools.product(fixed.items(),posed.items()):
                b1,b2=s1.BoundingBox(),s2.BoundingBox()
                if any(getattr(b1,c+'max')<=getattr(b2,c+'min') or getattr(b2,c+'max')<=getattr(b1,c+'min') for c in 'xyz'):continue
                volume=float(s1.intersect(s2).Volume())
                key=n1+' / '+n2
                if volume>.01 and (key not in worst or volume>worst[key]['volume_mm3']):
                    worst[key]={'volume_mm3':volume,'ankle_roll_rad':float(angle)}
        rows.append({'side':side,'range_rad':[lo,hi],'samples':17,'worst_intersections':worst})
    r={'scope':__doc__,'trial':str(a.trial),'rows':rows,
       'limitations':['discrete sweep, not continuous clearance proof','other robot parts outside this local ankle audit']}
    a.out.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))


if __name__=='__main__':main()
