#!/usr/bin/env python3
"""Compute CAD replacement mass ledger; hardware reservations remain unresolved."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import cadquery as cq
import numpy as np
from audit_r9_base_mass import audit


def aggregate(records):
    mass = sum(r['mass_kg'] for r in records.values())
    com = sum(r['mass_kg'] * np.array(r['com_base_m']) for r in records.values()) / mass
    inertia = np.zeros((3, 3))
    for r in records.values():
        d = np.array(r['com_base_m']) - com
        inertia += np.array(r['inertia_com_kg_m2']) + r['mass_kg'] * (d @ d * np.eye(3) - np.outer(d, d))
    return dict(mass_kg=mass, com_m=com.tolist(), inertia_kg_m2=inertia.tolist())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    baseline = audit(root)
    if not baseline['passed']:
        raise RuntimeError('Frozen baseline provenance mismatch')
    config_path = root / 'board/mechanical/engineering/rear_connection_candidate.json'
    config = json.loads(config_path.read_text())
    paths = {'body_shroud': config['assets']['body']['path'],
             'rear_cover': config['assets']['rear_plate']['path']}
    for side in ('left', 'right'):
        name = side + '_yaw_fixed_support'
        paths[name] = 'validation/inset_yaw_assembly_development_v1/yaw_inset_mount_v1/' + name + '.step'
    replacements = {}
    records = copy.deepcopy(baseline['components'])
    hashes = {str(config_path.relative_to(root)): hashlib.sha256(config_path.read_bytes()).hexdigest()}
    for name, relative in paths.items():
        path = root / relative
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        hashes[relative] = digest
        key = {'body_shroud': 'body', 'rear_cover': 'rear_plate'}.get(name)
        if key and digest != config['assets'][key]['sha256']:
            raise RuntimeError('Candidate source hash mismatch: ' + name)
        shape = cq.importers.importStep(str(path)).val()
        if not shape.isValid():
            raise RuntimeError('Invalid CAD: ' + name)
        volume = shape.Volume()
        density = 2700 if name == 'rear_cover' else 1270
        mass = volume * 1e-9 * density
        old = records[name]
        new = dict(mass_kg=mass, com_base_m=(np.array(shape.Center().toTuple())/1000).tolist(),
                   inertia_com_kg_m2=(np.array(cq.Shape.matrixOfInertia(shape))*mass/volume*1e-6).tolist(),
                   volume_mm3=volume, density_kg_m3=density, source=relative)
        # Geometry at old density plus material-density change sum to total delta.
        old_density = old['mass_kg']/old['volume_mm3']*1e9
        replacements[name] = dict(old=old, new=new, delta_mass_kg=mass-old['mass_kg'],
                                  geometry_delta_at_old_density_kg=(volume-old['volume_mm3'])*1e-9*old_density,
                                  density_delta_at_new_volume_kg=volume*1e-9*(density-old_density))
        records[name] = new
    combined = aggregate(records)
    result = dict(scope='Four CAD replacements only; retained reservations; not complete production mass or updated MuJoCo plant',
                  baseline=baseline['aggregate'], candidate_base=combined,
                  delta_base_mass_kg=combined['mass_kg']-baseline['aggregate']['mass_kg'],
                  replacements=replacements, components=records,
                  source_sha256=hashes,
                  unresolved=baseline['unresolved'] + ['Rear M3 hardware and yaw mounting hardware are not separately added; 25 g reservation retained without claiming coverage.',
                                                       'Unchanged printed parts retain frozen density; this is not a global material conversion.',
                                                       'Density assumes solid CAD volumes; slicer infill and print process are not calibrated.'])
    I = np.array(combined['inertia_kg_m2'])
    result['inertia_eigenvalues_kg_m2'] = np.linalg.eigvalsh(I).tolist()
    if min(result['inertia_eigenvalues_kg_m2']) <= 0:
        raise RuntimeError('Nonpositive inertia')
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ('candidate_base', 'delta_base_mass_kg')}, indent=2))


if __name__ == '__main__':
    main()
