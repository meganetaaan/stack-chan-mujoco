"""Measure the coverage of inherited rear-key envelopes; do not certify assembly."""
import argparse
import hashlib
import json
from pathlib import Path
import cadquery as cq
ROOT = Path(__file__).resolve().parents[3]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--out', type=Path, required=True)
a = p.parse_args()
a.out.mkdir(parents=True, exist_ok=True)
plan = {'question': 'Does the inherited tool envelope represent engagement and the complete tool?',
        'stop': 'Measure all eight key/bolt pairs once; no geometry optimization.',
        'acceptance': 'Assembly proof requires identified tool, socket engagement, handle and insertion path; a front-face-only cylinder is insufficient.'}
(a.out / 'plan.json').write_text(json.dumps(plan, indent=2)+'\n')
rows = []
sources = {}
for side in ['left', 'right']:
    for i in range(4):
        shapes = {}
        for kind in ['bolt', 'rear_key']:
            path = ROOT / f'validation/inset_yaw_assembly_development_v1/inset_fasteners_staged_v2/{side}_{i}_{kind}.step'
            sources[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
            shapes[kind] = cq.importers.importStep(str(path)).val().translate((-.2,0,0))
        key = shapes['rear_key'].BoundingBox()
        bolt = shapes['bolt'].BoundingBox()
        rows.append({'id': f'{side}_{i}', 'key_x_range_mm': [key.xmin,key.xmax],
                     'key_diameter_mm': key.ylen, 'key_length_mm': key.xlen,
                     'bolt_rear_face_x_mm': bolt.xmin,
                     'modeled_insertion_past_head_face_mm': max(0,key.xmax-bolt.xmin),
                     'head_face_gap_mm': bolt.xmin-key.xmax,
                     'handle_modeled': False, 'socket_modeled': False,
                     'complete_tool_coverage': False})
report = {'rows':rows, 'source_sha256':sources,
          'assembly_proven':False,
          'finding':'All inherited cylinders terminate at the bolt head face; no socket engagement or handle is modeled.',
          'prior_results':'Retain prior nominal cylinder clearance results; do not interpret them as actual tool access qualification.'}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'pairs':len(rows),'max_modeled_insertion_mm':max(r['modeled_insertion_past_head_face_mm'] for r in rows),'assembly_proven':False}))
