"""Bound stock thickness and main screw length without conflating tip position and protrusion."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import cadquery as cq

ROOT = Path(__file__).resolve().parents[3]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--out', type=Path, required=True)
a = p.parse_args()
a.out.mkdir(parents=True, exist_ok=False)
sources = {}
def read(rel, shift=None):
    path = ROOT / rel
    sources[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    shape = cq.importers.importStep(str(path)).val()
    return shape.translate(shift) if shift else shape

specpath = 'docs/prototype/mechanical/yaw_support/rear_bolt_candidate.json'
sources[specpath] = hashlib.sha256((ROOT / specpath).read_bytes()).hexdigest()
length = json.loads((ROOT / specpath).read_text())['length_mm']
plan = {
    'question': 'Effect of 3 mm stock +/-0.13 mm and specified M3 length on backing engagement and tip position',
    'stop': 'All eight main and four keeper axial stacks; no further mesh or parameter sweep',
    'assumptions': ['Backing contact entry remains fixed; stock thickness changes exit face only',
                    'Other seats and dimensions nominal; washer seating not qualified',
                    'Keeper length nominal only; no manufactured thread/chamfer modeled'],
    'stock_source': 'https://okouchi.co.jp/data/202410/A5052P-H34.pdf',
    'acceptance': 'Shaft reaches through plate for these bounds; this is not thread retention or full clearance acceptance',
}
(a.out / 'plan.json').write_text(json.dumps(plan, indent=2) + '\n')
rows = []
for side in ['left', 'right']:
    bar = read(f'validation/yaw_backing_keeper_v2/{side}_threaded_backing_plate.step').BoundingBox()
    assert abs(bar.xlen - 3) < 1e-5
    parts = [(f'{side}_main_{i}',
              read(f'validation/inset_yaw_assembly_development_v1/inset_fasteners_staged_v2/{side}_{i}_bolt.step', (-.2,0,0)),
              [length['min']-length['nominal'], length['max']-length['nominal']]) for i in range(4)]
    parts += [(f'{side}_keeper_{z}', read(f'validation/yaw_backing_keeper_v2/{side}_{z}_keeper_envelope.step'), [0]) for z in [64,76]]
    for name, screw, deltas in parts:
        tip = screw.BoundingBox().xmax
        cases = []
        for thickness, delta in itertools.product([2.87,3.13], deltas):
            end = bar.xmin + thickness
            actual_tip = tip + delta
            cases.append({'stock_thickness_mm': thickness, 'length_delta_mm': delta,
                          'exit_x_mm': end, 'tip_x_mm': actual_tip,
                          'protrusion_mm': actual_tip-end,
                          'shaft_material_overlap_mm': min(thickness,max(0,actual_tip-bar.xmin))})
        rows.append({'name':name,'entry_x_mm':bar.xmin,'nominal_tip_x_mm':tip,'cases':cases})
report = {'rows':rows,'source_sha256':sources,
          'all_tips_through_for_declared_bounds':all(c['protrusion_mm']>0 for r in rows for c in r['cases']),
          'fully_formed_thread_engagement_min_mm':None,
          'neighbor_clearance_verified':False, 'retention_strength_verified':False,
          'manufacturing_release':False}
(a.out / 'report.json').write_text(json.dumps(report,indent=2)+'\n')
for kind in ['main','keeper']:
    cases = [c for r in rows if kind in r['name'] for c in r['cases']]
    print(kind, 'protrusion mm', min(c['protrusion_mm'] for c in cases), max(c['protrusion_mm'] for c in cases))
