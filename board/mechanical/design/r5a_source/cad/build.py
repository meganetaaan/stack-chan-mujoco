#!/usr/bin/env python3
"""R5 body variants. All R4 leg parts are reused without changing local geometry,
link frames, joint axes, spacings, motor selection, or boot dimensions.
CAD axes: +X forward, +Y robot left, +Z up. Local base Z=0 is body underside.
"""
from pathlib import Path
import sys,json,numpy as np
import cadquery as cq
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from tab5_biped.core import PARAMS as P,KIN
import r4_geometry as R4
from r4_geometry import Part,box,cyl,union,CB,posed,mass_properties


def build():
    original=R4.build()
    legacy={p.name:p for p in original}
    A=P['body']['tab5_orientation']=='landscape'
    W=128.;H=128.;D=128. if A else 80.;w=P['body']['wall_mm']
    front=D/2;rear=-D/2;back=rear+w;device_back=front-12.;device_gap=.4
    out=[]
    def add(name,s,role='custom',col='shell',mass=None,collisions=None,note=''):
        if not s.isValid() or len(s.Solids())!=1 or s.Volume()<=0:
            raise ValueError(f'{name}: invalid or not a single solid ({len(s.Solids())})')
        out.append(Part(name,'base',s.clean(),role,R4.C[col],mass,collisions or [],note))
    # A closed monocoque except for device aperture, rear service panel and
    # the physically cut, motion-derived underside opening. No side slits.
    outer=box((D,W,H),(0,0,H/2),r=.65,edge='|X')
    cavity=box((D-2*w,W-2*w,H-2*w),(0,0,H/2))
    shell=outer.cut(cavity)
    shell=shell.cut(box((10,W+4,H+4),(rear-5+w,0,H/2)))
    if A:
        shell=shell.cut(box((20,W+4,82),(front-2.4,0,88.6))) # x starts51.6; z47.6
    else:
        shell=shell.cut(box((20,80.8,H+4),(front-2.4,0,H/2)))
    # Insert the motion envelope as one union of left/right swept footprints.
    polygons=json.loads((ROOT/'docs/underside_cutouts.json').read_text())
    for points in polygons.values():
        cutter=cq.Workplane('XY',origin=(0,0,-2)).polyline(points).close().extrude(4.2).val()
        shell=shell.cut(cutter)
    # Tab5 mounting follows the unchanged four holes, rotated with the device.
    ys=(-60,60) if A else (-36,36)
    zs=(52,124) if A else (4,124)
    for y in ys:
        for z in zs:
            start=device_back-(6.4 if z==124 or A else 3.1)
            end=device_back-device_gap
            boss=cyl(3.7,end-start,(start,y,z),(1,0,0))
            if not A:
                # Inward-pointing corner fingers connect the enlarged wings
                # to the original device's four mounting positions.
                sg=1 if y>0 else -1
                web=box((end-start,27.,7.4),((start+end)/2,sg*49.5,z))
                boss=boss.fuse(web)
            shell=shell.fuse(boss)
            shell=shell.cut(cyl(1.7,end-start+1,(start-.5,y,z),(1,0,0)))
    # Rear cover screw bosses are now near the widened body's corners.
    for y in (-59,59):
        for z in (8,120):
            shell=shell.fuse(cyl(4.6,6,(back,y,z),(1,0,0)))
            shell=shell.cut(cyl(1.25,6.4,(back-.2,y,z),(1,0,0)))
    if A:
        # An enclosure-side extension, NOT a change to the R4 servo cradles.
        # Its forward faces butt against the existing upper cradle bridges.
        cross=box((3,124.8,2.4),(back+1.5,0,51))
        rails=[box((24,24,2.4),(-50.2,sg*19,51)) for sg in (-1,1)]
        shell=union(shell,cross,*rails)
    # Conservative simplified physics collision panels preserve a larger
    # bottom aperture than the exact CAD contour. See model caveats in README.
    cols=[CB((D-12.4,w,H),(-6.2,s*(64-w/2),64)) for s in (-1,1)]
    cols.append(CB((D-12.4,W,w),(-6.2,0,128-w/2)))
    if A:cols.append(CB((w,W,47.6),(front-w/2,0,23.8)))
    else:cols.extend([CB((w,23.6,H),(front-w/2,s*52.2,64)) for s in (-1,1)])
    # Underside strips avoid the full sampled aperture bounding rectangle.
    cols.extend([CB((D-12.4,13.,w),(-6.2,s*57.5,w/2)) for s in (-1,1)])
    add('body_shroud',shell.clean(),collisions=cols,note='R5 motion-derived underside opening. Prototype Tab5 mounting fingers. No exterior side relief ports.')
    lid=box((w,W,H),(rear+w/2,0,H/2),r=.65,edge='|X')
    for y in (-59,59):
        for z in (8,120):lid=lid.cut(cyl(1.65,3,(rear-.5,y,z),(1,0,0)))
    for z in (102,108,114):lid=lid.cut(box((3,32,2.2),(rear+w/2,0,z),r=1,edge='|X'))
    add('rear_cover',lid,collisions=[CB((w,W,H),(rear+w/2,0,H/2))],note='Removable rear cover. Fastener engagement remains provisional.')
    if A:
        def landscape(s):
            return s.translate((0,0,-64)).rotate((0,0,0),(1,0,0),-90).translate((24,0,88))
        tab=landscape(legacy['Tab5'].shape)
        add('Tab5',tab,'hardware',mass=P['body']['tab5_mass_kg'],collisions=[CB((12,128,80),(58,0,88))],note='R4 physical device envelope rotated 90 degrees, upper edge aligned. Camera at side; screen graphics redrawn upright.')
        screen=box((.3,110.7,62.4),(63.85,-2.85,88),r=.25,edge='|X')
        plane=cq.Plane(origin=(63.9,0,0),xDir=(0,1,0),normal=(1,0,0))
        graphics=[cq.Workplane(plane).center(y,98).ellipse(4.3,5.2).extrude(.1).val() for y in (-22,22)]
        mouth=(cq.Workplane(plane).moveTo(-7,86).threePointArc((0,79),(7,86)).lineTo(5.3,86).threePointArc((0,80.7),(-5.3,86)).close().extrude(.1).val())
        graphics.append(mouth)
        for i,s in enumerate(graphics):
            screen=screen.cut(s);add('face_'+str(i),s,'visual','face',0)
        add('screen',screen,'visual','glass',0)
        add('camera',landscape(legacy['camera'].shape),'visual','glass',0)
    else:
        out.extend([p for p in original if p.name in ('Tab5','screen','camera','face_0','face_1','face_2')])
    # Battery, boards and their assumed masses remain at the R4 positions.
    out.extend([p for p in original if p.name in ('battery_2S_reservation','dedicated_5V_converter','TTL_interface','cables_and_fasteners')])
    # EXACT reuse. No unilateral mesh scaling and no hip-spacing change.
    out.extend([p for p in original if p.name.startswith(('left_','right_'))])
    return out

def export(parts):
    result=R4.export(parts)
    path=ROOT/'cad/step/assembly.step'
    text=path.read_text().replace('Tab5_R4_10DOF_Concealed','Tab5_R5_A_landscape_cube')
    path.write_text(text)
    return result
if __name__=='__main__':export(build())
