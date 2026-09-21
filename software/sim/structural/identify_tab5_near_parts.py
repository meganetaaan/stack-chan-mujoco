"""Identify source parts near Tab5; retain placement and source provenance."""
import argparse
import hashlib
import json
from pathlib import Path
import cadquery as cq

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--out', type=Path, required=True)
a = p.parse_args()
a.out.mkdir(parents=True, exist_ok=False)
tab_path = Path('software/sim/mujoco/assets/r9_fast_turn_v1/cad/Tab5.step')
assembly_path = Path('board/mechanical/prototype/yaw_support_candidate/revA/yaw_support_candidate.step')
body_path = Path('validation/yaw_tool_access_v1/body_shroud.step')
tab = cq.importers.importStep(str(tab_path)).val()
assembly = cq.importers.importStep(str(assembly_path)).val()
body = cq.importers.importStep(str(body_path)).val()
# An assembly compound can contain intentional overlapping hardware. It is
# not a fused Boolean solid; match the source against individual solids.
matches = []
for index, solid in enumerate(assembly.Solids()):
    if abs(solid.Volume() - body.Volume()) < 1e-6:
        if body.cut(solid).Volume() < 1e-6 and solid.cut(body).Volume() < 1e-6:
            matches.append(index)
if len(matches) != 1:
    raise ValueError('Body source has no unique matching assembly solid')
rows = []
for index, solid in enumerate(assembly.Solids()):
    rows.append({'solid_index': index, 'distance_mm': tab.distance(solid)})
body_distance = tab.distance(body)
minimum = min(r['distance_mm'] for r in rows)
report = {
    'assembly_minimum_mm': minimum,
    'body_shroud_distance_mm': body_distance,
    'body_matching_solid_index': matches[0],
    'body_attains_assembly_minimum': abs(minimum - body_distance) < 1e-7,
    'assembly_solid_distances': rows,
    'sources_sha256': {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                       for path in [tab_path, assembly_path, body_path]},
    'scope': 'Nominal static source attribution, not tolerance or dynamic qualification',
    'manufacturing_release': False,
}
(a.out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({k: v for k, v in report.items() if k not in ['assembly_solid_distances', 'sources_sha256']}))
