"""Promote already-screened v7 geometry to a canonical candidate, not a release."""
import hashlib
import json
import shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
base=ROOT/'board/mechanical/prototype/yaw_support_candidate'
src=ROOT/'validation/yaw_integrated_candidate_v7'
dst=base/'revC'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
proofs=[ROOT/'validation/yaw_v7_clearance_subset_v1/report.json',src/'all_pair_overlap_report.json']
for p in proofs:
    proof=json.loads(p.read_text())
    for path,expected in proof['source_sha256'].items():
        assert sha(ROOT/path)==expected, path
prior=ROOT/'validation/yaw_integrated_motion_v6/report.json'
for row in json.loads(prior.read_text())['results']:
    for path, expected in row['cad_sha256'].items():
        assert sha(ROOT/path)==expected, path
subset=json.loads(proofs[0].read_text())
assert subset['unchanged_parts']==50
assert all(x['new_material_outside_old_mm3']<1e-6 for x in subset['subset_checks'])
assert all(x['passed_screen'] for x in subset['inherited_rigid_clearance'])
overlap=json.loads(proofs[1].read_text())
assert overlap['pairs_tested']==1326
assert not any(x['increase_flag'] for x in overlap['nonzero_pairs'])
old=json.loads((base/'revB/inventory.json').read_text())
new=json.loads((src/'inventory.json').read_text())
a={x['name']:x for x in old['parts']}; b={x['name']:x for x in new['parts']}
assert a.keys()==b.keys() and len(b)==52
for x in new['parts']:
    if x.get('source'):
        assert sha(ROOT/x['source'])==x['source_sha256'],x['source']
changes=[{'part':n,'old_volume_mm3':a[n]['volume_mm3'],'new_volume_mm3':b[n]['volume_mm3'],
          'volume_delta_mm3':b[n]['volume_mm3']-a[n]['volume_mm3']}
         for n in b if a[n]!=b[n]]
dst.mkdir(exist_ok=True)
for name in ['inventory.json','geometric_moments.json','yaw_support_candidate.step']:
    shutil.copyfile(src/name,dst/name)
report={'source_sha256':{str(p.relative_to(ROOT)):sha(p) for p in proofs+[base/'revB/inventory.json',src/'inventory.json',src/'geometric_moments.json',src/'yaw_support_candidate.step']},
        'copies_byte_identical':all(sha(src/n)==sha(dst/n) for n in ['inventory.json','geometric_moments.json','yaw_support_candidate.step']),
        'changed_inventory_entries_from_revB':changes,'part_count':52,
        'inherited_rigid_clearance_scope':'yaw coupler/cradle versus fixed v7, +/-15 degrees; no new sweep',
        'minimum_inherited_residual_mm':min(x['residual_lower_bound_mm'] for x in subset['inherited_rigid_clearance']),
        'strength_verified':False,'whole_body_clearance_verified':False,'manufacturing_release':False,
        'excluded':'Pololu mount and updated rear plate, complete legs, current foot, harness, and newly selected power electronics are not combined in this subassembly'}
(dst/'change_check.json').write_text(json.dumps(report,indent=2)+'\n')
pointer={'revision':'revC','inventory':str((dst/'inventory.json').relative_to(ROOT)),
         'assembly':str((dst/'yaw_support_candidate.step').relative_to(ROOT)),
         'status':'design_candidate_not_released','source_candidate':'validation/yaw_integrated_candidate_v7',
         'evidence':str((dst/'change_check.json').relative_to(ROOT)),
         'legacy_analysis':'revB strength/mass/fit results are historical; evaluate applicability by source hashes, not current pointer.',
         'manufacturing_release':False}
(base/'current.json').write_text(json.dumps(pointer,indent=2)+'\n')
print(json.dumps({'parts':52,'changed_entries':len(changes),'copy_match':report['copies_byte_identical'],'manufacturing_release':False}))
