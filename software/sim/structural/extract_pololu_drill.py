"""Extract crosshair centers from the pinned manufacturer drill guide.
DXF has no unit metadata. Inch scale is checked against dimensioned PDF;
coordinates remain in DXF view, with no electrical pin/view assignment.
"""
import argparse
import hashlib
import json
from pathlib import Path
import ezdxf

p = argparse.ArgumentParser()
p.add_argument('dxf', type=Path)
p.add_argument('--out', type=Path, required=True)
a = p.parse_args()
expected = 'c7cbd3fda37bf437830d6c13a6db93bc9ff83f61b88f11353d4b6c8d3a35c5f3'
assert hashlib.sha256(a.dxf.read_bytes()).hexdigest() == expected
segments = []
for entity in ezdxf.readfile(a.dxf).modelspace():
    assert entity.dxftype() == 'POLYLINE'
    points = list(entity.points())
    if len(points) == 2:
        segments.append(points)
# Four outline strokes establish the local origin and dimensions.
outline = {(round(q.x, 6), round(q.y, 6)) for pair in segments[:4] for q in pair}
assert outline == {(7.5, 15.0), (9.2, 15.0), (7.5, 16.25), (9.2, 16.25)}
assert abs(1.7*25.4-43.2)<0.05 and abs(1.25*25.4-31.8)<0.051
# Crosshair strokes have equal lengths, except 0.0001 inch export rounding.
centers = []
for s, t in segments:
    if abs(s.y-t.y) > 1e-8:
        continue
    x, y, width = (s.x+t.x)/2, s.y, abs(t.x-s.x)
    for u, v in segments:
        if (abs(u.x-v.x) < 1e-8 and abs(u.x-x) < 0.00006
                and abs((u.y+v.y)/2-y) < 1e-8
                and abs(abs(v.y-u.y)-width) < 0.00011):
            centers.append({'center_dxf': [x,y],
                'center_local_mm': [round((x-7.5)*25.4,6), round((y-15)*25.4,6)],
                'cross_width_mm': round(width*25.4,6)})
assert len(centers) == 23, len(centers)
mounts = [c for c in centers if abs(c['cross_width_mm']-2.1844)<0.003
          and (c['center_dxf'][0]<7.6 or c['center_dxf'][0]>9.1)]
assert len(mounts) == 4
xs = sorted(set(c['center_local_mm'][0] for c in mounts))
ys = sorted(set(c['center_local_mm'][1] for c in mounts))
assert len(xs)==len(ys)==2
assert abs(xs[1]-xs[0]-38.9)<0.05
assert abs(ys[1]-ys[0]-25.4)<0.05
r = {'source_sha256':expected,'unit_metadata':None,
     'scale_basis':'25.4 mm/in inferred and checked against PDF board and mounting dimensions',
     'frame':'DXF view: origin at board lower-left (7.5,15); X long edge, Y short edge; not mapped to top/bottom view or robot',
     'board_mm':[43.18,31.75], 'mount_centers_mm':[c['center_local_mm'] for c in mounts],
     'mount_pitch_mm':[round(xs[1]-xs[0],6),round(ys[1]-ys[0],6)],
     'edge_offsets_mm':{'x':[xs[0],round(43.18-xs[1],6)],'y':[ys[0],round(31.75-ys[1],6)]},
     'all_crosshairs':centers,'electrical_mapping_verified':False,
     'limitations':['Cross widths are drawing symbols, not independently verified drill diameters.',
                     'Manufacturing tolerances from PDF still apply; exported decimals are not accuracy claims.',
                     'Component keepouts, screw heads, spacers and board orientation still require STEP/view verification.']}
a.out.parent.mkdir(parents=True,exist_ok=True)
a.out.write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps({k:r[k] for k in ['mount_centers_mm','mount_pitch_mm','edge_offsets_mm']}))
