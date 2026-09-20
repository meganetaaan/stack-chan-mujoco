#!/usr/bin/env python3
"""Build the forward battery tray concept; not a complete dynamics candidate."""
import argparse
import hashlib
import json
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error('new output required')
    cad_source = Path('outputs/design_r6_base_collisions/cad').resolve()
    sys.path.insert(0, str(cad_source))
    import cadquery as cq
    from r4_geometry import Part, box, union, mass_properties
    concept_path = Path('design/battery_mount_concept.json')
    concept = json.loads(concept_path.read_text())
    blocks = []
    for item in [concept['tray_floor'], *concept['long_walls'], *concept['corner_end_stops']]:
        center = list(item['center_mm'])
        center[0] += 30
        blocks.append((item['size_mm'], center))
    for sign in [-1, 1]:
        blocks.extend([([6, 26, 3], [29, sign*49, 60.05]),
                       ([6, 2, 8], [29, sign*61.2, 62])])
    tray = union(*(box(size, center) for size, center in blocks))
    for sign in [-1, 1]:
        hole = cq.Solid.makeCylinder(1.1, 4, cq.Vector(29, sign*59.2, 63), cq.Vector(0, sign, 0))
        tray = tray.cut(hole)
    tray = tray.clean()
    if not tray.isValid() or len(tray.Solids()) != 1:
        raise ValueError('tray must be one connected valid solid')
    mass, com, inertia = mass_properties(Part('fast_turn_battery_tray', 'base', tray, 'custom', (.25,.25,.3), None))
    battery = box(concept['battery_size_mm'], [29, 0, 80])
    overlap = float(tray.intersect(battery).Volume())
    if overlap > .001:
        raise ValueError('tray intersects battery envelope')
    args.out.mkdir(parents=True)
    cq.exporters.export(tray, str(args.out/'battery_tray.step'))
    cq.exporters.export(tray, str(args.out/'battery_tray.stl'), tolerance=.09, angularTolerance=.15)
    cq.exporters.export(battery, str(args.out/'battery_envelope.step'))
    report = {'scope': __doc__, 'valid': True, 'solid_count': 1,
              'battery_intersection_mm3': overlap, 'mass_kg': float(mass),
              'com_base_m': com.tolist(), 'inertia_com_kg_m2': inertia.tolist(),
              'collision_boxes_mm': [{'size': s, 'center': c} for s, c in blocks],
              'mount_holes': {'diameter_mm': 2.2, 'centers_mm': [[29,-61.2,63],[29,61.2,63]], 'axis': 'y'},
              'not_verified': ['sidewall holes and reinforcing bosses', 'strength',
                               'complete fixed-component CAD interference including converter',
                               'full moving CAD assembly', 'mass of fasteners', 'dynamics'],
              'source_sha256': {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in [Path(__file__), concept_path, cad_source/'r4_geometry.py']}}
    (args.out/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k: report[k] for k in ['valid', 'solid_count', 'battery_intersection_mm3', 'mass_kg']}))


if __name__ == '__main__':
    main()
