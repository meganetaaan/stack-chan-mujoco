"""Screen thicker sole seat recessed into yoke; not a strength qualification."""
import argparse, hashlib, json
from pathlib import Path
import cadquery as cq

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--out', type=Path, required=True)
p.add_argument('--slide-channel', action='store_true')
p.add_argument('--open-channel-end', action='store_true', help='Extend channel beyond outer face, removing 0.2 mm end wall')
a = p.parse_args()
if a.open_channel_end and not a.slide_channel:
    p.error('--open-channel-end requires --slide-channel')
a.out.mkdir(parents=True, exist_ok=False)
rows = []
for side, cy in [('left', 6), ('right', -6)]:
    paths = {
        'holder': Path(f'validation/sole_clamp_seat_v1/{side}_holder_envelope.step'),
        'yoke': Path(f'validation/rigid_sole_keyhole_v1/{side}_yoke.step'),
        'screw': Path(f'validation/sole_external_nut_v1/{side}_screw.step'),
        'boot': Path(f'validation/boot_low_head_candidate_v1/cad/{side}_boot_shell.step'),
    }
    parts = {k: cq.importers.importStep(str(v)).val() for k, v in paths.items()}
    def cyl(r, z, h):
        return cq.Solid.makeCylinder(r, h, cq.Vector(35, cy, z))
    # Raise bearing seat 1 mm into the 3 mm yoke; maintain head and floor height.
    holder = parts['holder'].fuse(cyl(3.21, -19.6, 1.6)).cut(cyl(1.15, -19.61, 1.62)).clean()
    pocket = cyl(3.8, -19.01, 1.01)
    if a.slide_channel:
        travel = 9 if a.open_channel_end else 8
        pocket = pocket.fuse(pocket.translate((travel, 0, 0))).fuse(cq.Solid.makeBox(travel, 7.6, 1.01, cq.Vector(35, cy - 3.8, -19.01)))
    yoke = parts['yoke'].cut(pocket).clean()
    assert holder.isValid() and len(holder.Solids()) == 1
    assert yoke.isValid() and len(yoke.Solids()) == 1
    for name, shape in [('holder_envelope', holder), ('yoke', yoke)]:
        cq.exporters.export(shape, str(a.out / f'{side}_{name}.step'))
    # The raised seat may block the existing slide path: test it explicitly.
    slide = [{'x_mm': x / 2, 'overlap_mm3': holder.translate((x / 2, 0, 0)).intersect(yoke).Volume()} for x in range(17)]
    rows.append({
        'side': side,
        'source_sha256': {k: hashlib.sha256(v.read_bytes()).hexdigest() for k, v in paths.items()},
        'holder_volume_delta_mm3': holder.Volume() - parts['holder'].Volume(),
        'yoke_volume_delta_mm3': yoke.Volume() - parts['yoke'].Volume(),
        'aligned_overlap_mm3': {k: holder.intersect(v).Volume() for k, v in {'yoke': yoke, 'screw': parts['screw'], 'boot': parts['boot']}.items()},
        'slide_samples': slide,
        'slide_max_overlap_mm3': max(r['overlap_mm3'] for r in slide),
    })
report = {'rows': rows, 'open_channel_end': a.open_channel_end, 'slide_channel': a.slide_channel, 'seat_thickness_mm': 1.6, 'yoke_local_remaining_thickness_mm': 2,
          'head_floor_clearance_mm': .8, 'manufacturing_release': False,
          'note': 'Aligned clearance alone does not prove assembly; sliding seat must enter pocket.'}
(a.out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report))
