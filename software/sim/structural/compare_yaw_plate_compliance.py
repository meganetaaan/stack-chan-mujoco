"""Bounded unit-load comparison; not a bolted-joint strength qualification."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from elasticity import tetrahedralize, analyze_many

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--out', type=Path, required=True)
a = p.parse_args()
a.out.mkdir(parents=True, exist_ok=False)
plan = {
    'question': 'Effect of outer connector opening on metal plate elastic compliance.',
    'scope': 'Left plate only, linear unit-load comparison; not actual joint contact.',
    'material_assumption': {'young_MPa': 193000, 'poisson': .3},
    'boundary_assumption': 'Top Z89 face patches within radius 2.5 mm of screw axes; centroid-selected facets. Support axes X=-34,8.1 Y=16,36; load axes X=-27.5,2.5 Y=18,34.',
    'loads': 'Unit Fz, Mx, My about (-12.5,26,89); N and N mm.',
    'supports': ['clamped', 'normal_z'],
    'mesh_sizes_mm': [1.5, 1.0],
    'stop': 'Exactly two shapes, two mesh sizes, two support assumptions and three unit loads. No stress-driven refinement.',
    'numerical_criteria': 'Force/moment assembly checked by solver; residual <1e-7 N; 2*energy/work within 1e-6; fine/coarse compliance change <=10% for quantitative comparison, otherwise inconclusive.',
    'limits': 'Patch area changes with mesh. No preload, unilateral contact, bolt flexibility, shelf deformation, fatigue, or material certification. No manufacturing release from this comparison.'
}
(a.out/'plan.json').write_text(json.dumps(plan, indent=2)+'\n')
def patches(xs, ys):
    def selector(x):
        inside = np.zeros(x.shape[1:], dtype=bool)
        for cx in xs:
            for cy in ys:
                inside |= (x[0]-cx)**2+(x[1]-cy)**2 <= 2.5**2
        return np.isclose(x[2], 89, atol=1e-7) & inside
    return selector
fixed = patches([-34,8.1], [16,36])
loaded = patches([-27.5,2.5], [18,34])
loads = [[0,0,1,0,0,0], [0,0,0,1,0,0], [0,0,0,0,1,0]]
rows = []
hashes = {}
for shape, path in [('old','validation/yaw_metal_seat_v4/left_mount_plate.step'), ('relief','validation/yaw_connector_plate_relief_v2/left_mount_plate.step')]:
    hashes[path] = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    for size in plan['mesh_sizes_mm']:
        mesh = tetrahedralize(path, a.out/f'{shape}_{size}.msh', size)
        for mode in plan['supports']:
            for label, (report, _) in zip(['Fz','Mx','My'], analyze_many(mesh, fixed, loaded, [-12.5,26,89], loads, young=193000, poisson=.3, support_mode=mode)):
                report.update(shape=shape, mesh_size_mm=size, load=label)
                report['numerical_balance_pass'] = bool(report['free_residual_norm_N'] < 1e-7 and abs(2*report['strain_energy_Nmm']/report['external_work_Nmm']-1) < 1e-6)
                rows.append(report)
                (a.out/'report.json').write_text(json.dumps({'source_sha256':hashes,'rows':rows,'manufacturing_release':False}, indent=2)+'\n')
                print(shape, size, mode, label, report['external_work_Nmm'], flush=True)
comparisons = []
for mode in plan['supports']:
    for label in ['Fz','Mx','My']:
        values = {(r['shape'],r['mesh_size_mm']):r['external_work_Nmm'] for r in rows if r['support_mode']==mode and r['load']==label}
        changes = {s:abs(values[s,1.0]/values[s,1.5]-1) for s in ['old','relief']}
        comparisons.append({'support':mode,'load':label,'fine_relief_to_old_compliance_ratio':values['relief',1.0]/values['old',1.0], 'mesh_relative_changes':changes,'quantitative_comparison_eligible':max(changes.values())<=.1})
(a.out/'comparison.json').write_text(json.dumps(comparisons,indent=2)+'\n')
