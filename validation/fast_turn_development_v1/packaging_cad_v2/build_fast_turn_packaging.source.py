#!/usr/bin/env python3
"""CAD packaging development: fixed parts and yaw couplers, not a full robot."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import sys
import numpy as np


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    if a.out.exists():
        p.error('new output required')
    source = Path('outputs/design_r6_base_collisions').resolve()
    sys.path[:0] = [str(source/'cad'), str(source/'src')]
    import cadquery as cq
    from build import build
    from r4_geometry import Part, box, cyl, union, mass_properties
    original = {part.name: part for part in build() if part.role != 'visual'}
    baseline = Path('assets/r8_yaw_offset_flange_v1')
    mount = Path('validation/battery_mount_review_v2')
    manifest = json.loads((baseline/'CANDIDATE.json').read_text())
    shapes = {}
    records = {r['part']: r for r in manifest['fixed_base_parts']}
    for name in records:
        paths = [baseline/'cad'/(name+'.step'), mount/(name+'.step')]
        available = next((path for path in paths if path.exists()), None)
        shapes[name] = cq.importers.importStep(str(available)).val() if available else original[name].shape
        if name == 'TTL_interface':
            shapes[name] = shapes[name].translate((0,0,12))

    def intersections(parts):
        rows = []
        for (n1,s1),(n2,s2) in itertools.combinations(parts.items(), 2):
            b1,b2 = s1.BoundingBox(),s2.BoundingBox()
            if any(getattr(b1,axis+'max') <= getattr(b2,axis+'min') or
                   getattr(b2,axis+'max') <= getattr(b1,axis+'min') for axis in 'xyz'):
                continue
            v = float(s1.intersect(s2).Volume())
            if v > .01:
                rows.append({'parts': [n1,n2], 'volume_mm3': v})
        return rows

    before = intersections(shapes)
    shapes.pop('battery_M3_envelope_0')
    shapes.pop('battery_M3_envelope_1')
    for name in ['battery_2S_reservation', 'battery_strap_envelope']:
        shapes[name] = shapes[name].translate((30,0,0))
    shapes['battery_tray'] = cq.importers.importStep(
        'validation/fast_turn_development_v1/tray_cad_v1/battery_tray.step').val()
    # Move the converter behind the yaw cases; keep the existing envelope/mass.
    shapes['dedicated_5V_converter'] = shapes['dedicated_5V_converter'].translate((-58,0,0))
    moving = {}
    for side, sign in [('left',1),('right',-1)]:
        y = sign*26
        name = side+'_yaw_motor_case'
        shapes[name] = shapes[name].translate((20,sign*4,0))
        # Keep the rear upright anchored at its old x position, extend the shelf.
        shapes[side+'_yaw_fixed_support'] = union(
            box((71.5,36,3),(-25.75,y,89.5)), box((3,20,40.2),(-60,y,70)))
        plate = box((35,22,3),(-16.5,y,52.9))
        post = cyl(4,8,(-5,y,53.5))
        flange = cyl(8,2,(-5,y,60))
        for dx,dy in [(6,0),(0,6),(-6,0),(0,-6)]:
            flange = flange.cut(cyl(1.1,3,(-5+dx,y+dy,59.5)))
        moving[side+'_yaw_coupler'] = union(plate,post,flange)
        shapes[side+'_battery_screw_envelope'] = box((4,6,4),(29,sign*61,63))
    after = intersections(shapes)
    a.out.mkdir(parents=True)
    properties = {}
    for name, shape in {**shapes, **moving}.items():
        if not shape.isValid() or len(shape.Solids()) != 1:
            raise ValueError(name + ': invalid or disconnected solid')
        # Retain explicitly specified hardware masses. New screws are envelope-only.
        hardware = name in ['Tab5','battery_2S_reservation','dedicated_5V_converter',
                            'TTL_interface','cables_and_fasteners','battery_strap_envelope'] or name.endswith('_yaw_motor_case')
        mass = records[name]['mass_kg'] if hardware else None
        m,com,I = mass_properties(Part(name,'base',shape,'custom',(.25,.3,.35),mass))
        properties[name] = {'mass_kg': float(m), 'com_base_m': com.tolist(),
                            'inertia_com_kg_m2': I.tolist(),
                            'volume_mm3': float(shape.Volume()),
                            'mass_valid_for_dynamics': not name.endswith('_screw_envelope')}
        cq.exporters.export(shape,str(a.out/(name+'.step')))
        cq.exporters.export(shape,str(a.out/(name+'.stl')),tolerance=.09,angularTolerance=.15)
    report = {'scope': __doc__, 'baseline_fixed_intersections': before,
              'candidate_fixed_intersections': after, 'properties': properties,
              'not_verified': ['full leg CAD and swept clearance', 'mount fasteners and strength',
                               'new screw masses', 'coupler engagement with cradle',
                               'physical turning time and stability'],
              'source_sha256': {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                                for path in [Path(__file__), baseline/'CANDIDATE.json',
                                             source/'cad/build.py', source/'cad/r4_geometry.py']}}
    (a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'baseline_fixed_intersections': before, 'candidate_fixed_intersections': after}))


if __name__ == '__main__':
    main()
