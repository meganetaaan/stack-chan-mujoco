#!/usr/bin/env python3
"""Screen paired vertical servo CASE envelopes inside the current torso CAD.

Nominal static packaging only. Shaft alignment, brackets, rotating-leg sweeps,
bearings, cabling, strength and kinematics are deliberately not claimed here.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--design', type=Path, required=True)
    p.add_argument('--mount', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--ttl-shift-z-mm', type=float, default=0., help='hypothetical internal board relocation; mounting not designed')
    a = p.parse_args()
    if a.out.exists():
        p.error('new output path required')
    design = a.design.resolve()
    sys.path[:0] = [str(design/'cad'), str(design/'src')]
    import cadquery as cq
    from build import build
    from r4_geometry import box, posed
    from tab5_biped.core import nominal, all_frames
    q, base = nominal()
    frames = all_frames(q, base)
    parts = {part.name: part for part in build() if part.role != 'visual'}
    added = ['body_shroud', 'battery_2S_reservation', 'battery_tray',
             'battery_strap_envelope', 'battery_M3_envelope_0', 'battery_M3_envelope_1']
    for name in added:
        parts[name] = SimpleNamespace(shape=cq.importers.importStep(str(a.mount/(name+'.step'))).val(), link='base')
    if a.ttl_shift_z_mm:
        parts['TTL_interface'].shape = parts['TTL_interface'].shape.translate((0, 0, a.ttl_shift_z_mm))
    world = {name: posed(part.shape, frames[part.link]) for name, part in parts.items()}
    board_findings = []
    if a.ttl_shift_z_mm:
        for name, shape in world.items():
            if name == 'TTL_interface':continue
            volume = world['TTL_interface'].intersect(shape).Volume()
            if volume > .01:board_findings.append({'part': name, 'overlap_mm3': volume})
    cases = []
    for x in [-35., -25., -15.]:
        for z in [65., 75., 90.]:
            findings = []
            for side, y in [('left', 22.), ('right', -22.)]:
                envelope = posed(box((20., 34., 26.), (x, y, z)), frames['base'])
                for name, shape in world.items():
                    first, second = envelope.BoundingBox(), shape.BoundingBox()
                    if any(getattr(first, axis+'max') <= getattr(second, axis+'min') or
                           getattr(second, axis+'max') <= getattr(first, axis+'min') for axis in 'xyz'):
                        continue
                    volume = envelope.intersect(shape).Volume()
                    if volume > .01:
                        findings.append({'side': side, 'part': name, 'overlap_mm3': volume})
            cases.append({'center_x_mm': x, 'center_z_mm': z, 'center_y_mm': [22., -22.],
                          'nominal_case_envelopes_clear': not findings, 'intersections': findings})
    sources = [Path(__file__), design/'robot.json', design/'cad/build.py', design/'cad/r4_geometry.py',
               design/'src/tab5_biped/core.py', *[a.mount/(name+'.step') for name in added]]
    result = {'scope': __doc__, 'case_size_xyz_mm': [20., 34., 26.],
              'hypothetical_TTL_shift_z_mm': a.ttl_shift_z_mm,
              'relocated_TTL_intersections': board_findings,
              'case_dimensions_basis': 'existing robot.json XL330 case dimensions, reoriented with 26 mm along vertical; shaft offset not resolved',
              'pair_separation_mm': 44., 'pair_case_gap_y_mm': 10.,
              'unchanged': ['torso exterior', 'thigh length', 'shin length', 'foot outline', 'battery installed'],
              'not_verified': ['output shaft location', 'mounting and support bearings', 'joint sweep clearance',
                               'leg remounting geometry', 'cables and connector access', 'strength and dynamic behavior'],
              'source_sha256': {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in sources},
              'cases': cases}
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(cases, indent=2))


if __name__ == '__main__':
    main()
