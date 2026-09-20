#!/usr/bin/env python3
"""Build the internal battery tray concept and check static CAD intersections.

Produces a separate review assembly, not a dynamics model or manufacturing release.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--design', type=Path, required=True)
    parser.add_argument('--concept', type=Path, default=Path('design/battery_mount_concept.json'))
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error('use a new output directory')
    design = args.design.resolve()
    sys.path[:0] = [str(design/'cad'), str(design/'src')]
    import cadquery as cq
    from build import build
    from r4_geometry import box, cyl, union, posed
    from tab5_biped.core import all_frames, nominal, PARAMS
    c = json.loads(args.concept.read_text())
    components = [c['tray_floor']] + c['long_walls'] + c['corner_end_stops'] + c['mount_pads'] + c['support_webs']
    tray = union(*(box(x['size_mm'], x['center_mm']) for x in components))
    parts = {p.name: p for p in build() if p.role != 'visual'}
    body = parts['body_shroud'].shape
    old_body = body
    for hole in c['proposed_hole_axes']:
        cutter = cyl(hole['clearance_diameter_mm']/2, 7, (hole['x_mm'], hole['y_mm'], 49), (0, 0, 1))
        tray = tray.cut(cutter)
        body = body.cut(cutter)
    tray = tray.clean()
    if not tray.isValid() or len(tray.Solids()) != 1:
        raise ValueError('tray is not a valid single solid')
    battery = box(c['battery_size_mm'], c['battery_center_base_mm'])
    # Explicit geometric envelopes; no thread, preload or textile mechanics.
    outer = [(-13.65,58.8),(11.65,58.8),(11.65,69.0),(9.75,99.7),(-11.75,99.7),(-13.65,69.0)]
    inner = [(-13.15,59.3),(11.15,59.3),(11.15,68.8),(9.25,99.2),(-11.25,99.2),(-13.15,68.8)]
    def band_polygon(points):
        return cq.Workplane('XZ').polyline(points).close().extrude(c['strap']['width_mm']).val().translate((0,4,0))
    strap = band_polygon(outer).cut(band_polygon(inner)).clean()
    hardware = {'battery_strap_envelope': strap}
    for i, hole in enumerate(c['proposed_hole_axes']):
        x, y = hole['x_mm'], hole['y_mm']
        shaft = cyl(1.5,10,(x,y,45.1),(0,0,1))
        head = cyl(3,2,(x,y,55.1),(0,0,1))
        washer = cyl(3.5,.5,(x,y,54.6),(0,0,1))
        nut = cq.Workplane('XY',origin=(x,y,47.4)).polygon(6,6.35).extrude(2.4).val()
        hardware[f'battery_M3_envelope_{i}'] = union(shaft,head,washer,nut)
    for name, shape in hardware.items():
        if not shape.isValid() or len(shape.Solids()) != 1:
            raise ValueError(f'{name}: invalid envelope')
    replacements = {'body_shroud': body, 'battery_2S_reservation': battery}
    q, base = nominal()
    frames = all_frames(q, base)
    tray_world = posed(tray, frames['base'])
    checks = []
    for name, part in parts.items():
        shape = replacements.get(name, part.shape)
        world = posed(shape, frames[part.link])
        overlap = tray_world.intersect(world).Volume()
        checks.append({'part': name, 'overlap_mm3': overlap, 'distance_mm': tray_world.distance(world)})
    hardware_checks = []
    for name, shape in hardware.items():
        world = posed(shape, frames['base'])
        candidates = {n:posed(replacements.get(n,p.shape),frames[p.link]) for n,p in parts.items()}
        candidates['battery_tray'] = tray_world
        for other, candidate in candidates.items():
            overlap = world.intersect(candidate).Volume()
            if overlap > .01:
                hardware_checks.append({'a':name,'b':other,'overlap_mm3':overlap})
    removed = old_body.cut(body)
    density = PARAMS['mass_assumptions']['printed_density_kg_m3']
    printed_delta = (tray.Volume()-removed.Volume()) * 1e-9 * density
    assumed_other = c['strap']['mass_assumption_kg'] + c['fasteners']['quantity']*c['fasteners']['mass_assumption_each_kg']
    args.out.mkdir(parents=True)
    for name, shape in {'battery_tray': tray, **replacements, **hardware}.items():
        cq.exporters.export(shape, str(args.out/(name+'.step')))
        cq.exporters.export(shape, str(args.out/(name+'.stl')))
    assembly = cq.Assembly(name='battery_mount_review_only')
    for name, part in parts.items():
        assembly.add(posed(replacements.get(name, part.shape), frames[part.link]), name=name)
    assembly.add(tray_world, name='battery_tray')
    for name, shape in hardware.items():
        assembly.add(posed(shape,frames['base']),name=name)
    assembly.save(str(args.out/'assembly.step'))
    report = {
        'scope': 'Tray, internal rail holes, strap and fastener envelopes; nominal pose only; hardware masses remain assumptions',
        'manufacturing_release': False, 'dynamics_validated': False,
        'tray_valid_single_solid': True,
        'tray_volume_mm3': tray.Volume(), 'body_removed_volume_mm3': removed.Volume(),
        'printed_density_kg_m3': density, 'printed_mass_delta_kg': printed_delta,
        'strap_fastener_mass_assumption_kg': assumed_other,
        'total_mass_delta_kg': printed_delta+assumed_other,
        'nominal_tray_clear': all(x['overlap_mm3'] <= .01 for x in checks),
        'checks': checks,
        'hardware_intersections': hardware_checks,
        'nominal_hardware_clear': not hardware_checks,
        'hardware_caveats': 'Strap closure, thread fit, torque/preload, tolerances and textile deformation are not modeled. Fasteners are fused envelopes, not screw/nut contact simulations.',
        'battery_center_base_mm': c['battery_center_base_mm'],
        'input_sha256': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in [args.concept, Path(__file__), design/'robot.json', design/'cad/build.py', design/'cad/r4_geometry.py']},
        'remaining': ['moving-leg clearance', 'strap closure and fastener access', 'retention strength', 'connector and exchange access', 'collision and inertia regeneration', 'mounted model gait evaluation'],
    }
    (args.out/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('checks','input_sha256')}, indent=2))


if __name__ == '__main__':
    main()
