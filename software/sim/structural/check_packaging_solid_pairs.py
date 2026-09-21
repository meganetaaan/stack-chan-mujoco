"""Recheck a packaging report using solid pairs, not compound Booleans."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import cadquery as cq

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--report', type=Path, required=True)
p.add_argument('--out', type=Path, required=True)
a = p.parse_args()
a.out.mkdir(parents=True, exist_ok=False)
source = json.loads(a.report.read_text())
paths = list(source['sources_sha256'])
if len(paths) != len(source['groups']):
    raise ValueError('Expected one source file per ordered group')
shapes = {}
for name, filename in zip(source['groups'], paths):
    path = Path(filename)
    if hashlib.sha256(path.read_bytes()).hexdigest() != source['sources_sha256'][filename]:
        raise ValueError(f'Source changed: {path}')
    shapes[name] = cq.importers.importStep(str(path)).val().Solids()
rows = []
for (left, solids), (right, others) in itertools.combinations(shapes.items(), 2):
    details = []
    for i, solid in enumerate(solids):
        for j, other in enumerate(others):
            volume = solid.intersect(other).Volume()
            distance = solid.distance(other)
            details.append({'left_solid': i, 'right_solid': j,
                            'overlap_mm3': volume, 'distance_mm': distance})
    rows.append({'a': left, 'b': right,
                 'overlap_mm3': sum(d['overlap_mm3'] for d in details),
                 'distance_mm': min(d['distance_mm'] for d in details),
                 'solid_pairs': details})
old = {(r['a'], r['b']): r for r in source['checks']}
changes = []
for row in rows:
    previous = old[(row['a'], row['b'])]
    changes.append({'a': row['a'], 'b': row['b'],
                    'old_overlap_mm3': previous['overlap_mm3'],
                    'new_overlap_mm3': row['overlap_mm3'],
                    'distance_change_mm': row['distance_mm'] - previous['distance_mm']})
result = {
    'input_report': str(a.report),
    'input_report_sha256': hashlib.sha256(a.report.read_bytes()).hexdigest(),
    'sources_sha256': source['sources_sha256'],
    'checks': rows, 'comparison': changes,
    'nominal_cross_group_overlap_free': all(
        d['overlap_mm3'] < 1e-6 for r in rows for d in r['solid_pairs']),
    'scope': 'Cross-group solid pairs only; internal yaw joints and full motion excluded',
    'volume_meaning': 'Sum can double-count overlapping parts; use individual zero-intersection checks',
    'manufacturing_release': False,
}
(a.out / 'report.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({'group_pairs': len(rows),
                  'solid_pairs': sum(len(r['solid_pairs']) for r in rows),
                  'nominal_cross_group_overlap_free': result['nominal_cross_group_overlap_free'],
                  'nonzero': [r for r in changes if r['new_overlap_mm3'] >= 1e-6]}))
