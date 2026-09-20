#!/usr/bin/env python3
"""Screen miscellaneous mass allowance against existing hardware envelopes."""
import argparse
import hashlib
import json
from pathlib import Path
import cadquery as cq


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    root = Path(__file__).resolve().parents[3]
    config = json.loads((root/'board/mechanical/engineering/rear_connection_candidate.json').read_text())
    rear = (root/config['assets']['body']['path']).parent
    plate = (root/config['assets']['rear_plate']['path']).parent
    yaw = root/'validation/inset_yaw_assembly_development_v1/inset_fasteners_staged_v2'
    plan = json.loads((yaw/'plan.json').read_text())
    if plan['bolt_length_mm'] != 16:
        raise RuntimeError('Expected M3x16 development envelopes')
    paths = []
    for i in range(4):
        paths.extend(rear/f'corner_{i}_{kind}.step' for kind in ('bolt','nut','inner_washer'))
        paths.append(plate/f'corner_{i}_rear_washer.step')
    for side in ('left','right'):
        for i in range(4):
            paths.extend(yaw/f'{side}_{i}_{kind}.step' for kind in ('bolt','nut','inner_washer','rear_washer'))
    rows = []
    for path in paths:
        shape = cq.importers.importStep(str(path)).val()
        volume = shape.Volume()
        rows.append(dict(path=str(path.relative_to(root)), sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                         volume_mm3=volume, mass_kg=volume*1e-9*8000))
    total = sum(r['mass_kg'] for r in rows)
    report = dict(scope=__doc__, density_assumed_kg_m3=8000,
                  criteria={'allowance_must_cover_listed_hardware_kg': .025},
                  listed_hardware_mass_kg=total, remaining_allowance_kg=.025-total,
                  listed_hardware_only_fits=total <= .025,
                  complete_allowance_verified=False, rows=rows,
                  limitations=['8000 kg/m3 is an explicit screening assumption, not certified purchased-part density.',
                               'Nominal solid screw heads and thread/cylindrical nut envelopes are not exact purchased masses.',
                               'Yaw envelopes are from staged development CAD; positions and tolerance compatibility with the latest rear plate are not certified.',
                               'Harness, connectors, motor mounting fasteners, Tab5 hardware and other miscellaneous parts are not included.',
                               'Two dedicated tray screws are already outside the 25 g allowance and are excluded here.',
                               'Do not add these masses on top of the unchanged 25 g allowance without defining a new residual harness/other-hardware budget.'])
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k: report[k] for k in ('listed_hardware_mass_kg','remaining_allowance_kg','listed_hardware_only_fits')}, indent=2))


if __name__ == '__main__':
    main()
