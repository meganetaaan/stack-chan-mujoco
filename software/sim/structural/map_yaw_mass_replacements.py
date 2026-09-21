"""Map current yaw assembly to frozen base allocations, without assigning unknown material masses."""
import argparse,csv,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
root=Path(__file__).resolve().parents[3]
provenance=root/'validation/base_mass_provenance_development_v1/report.json'
old=json.loads(provenance.read_text())
for path,sha in old['source_sha256'].items():
 assert hashlib.sha256((root/path).read_bytes()).hexdigest()==sha, f'stale provenance: {path}'
latest=root/'board/mechanical/prototype/yaw_support_candidate/revA/inventory.json'
parts=json.loads(latest.read_text())['parts'];mapping={'body_shroud':'body_shroud','rear_plate':'rear_cover','left_yaw_fixed_support':'left_yaw_fixed_support','right_yaw_fixed_support':'right_yaw_fixed_support'}
rows=[]
for part in parts:
 n=part['name'];prior=mapping.get(n)
 new_structure=n.endswith(('threaded_backing_plate','mount_plate'))
 rows.append({'candidate_part':n,'model_body':'base','old_allocation':prior or ('none: additional structural plate' if new_structure else 'cables_and_fasteners reservation: reconcile'),'operation':'replace exact old component' if prior else ('add new structural component after old support replacement' if new_structure else 'resolve against reservation before addition'),'old_component_mass_kg':old['components'][prior]['mass_kg'] if prior else '', 'new_mass_kg':'','candidate_volume_mm3':part['volume_mm3']})
assert len(rows)==52 and len(mapping)==4
with (a.out/'replacement_map.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
removed=sum(old['components'][v]['mass_kg'] for v in mapping.values());retained=old['aggregate']['mass_kg']-removed
report={'source_sha256':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [provenance,latest]},'upstream_provenance_hashes_current':True,'frozen_base_mass_kg':old['aggregate']['mass_kg'],'four_replaced_allocations_kg':removed,'retained_before_reservation_reconciliation_kg':retained,'unitemized_cables_fasteners_reservation_kg':old['components']['cables_and_fasteners']['mass_kg'],'retained_excluding_that_reservation_kg':retained-old['components']['cables_and_fasteners']['mass_kg'],'mass_formula':'retained_excluding_reservation + four replacement masses + new structural/hardware masses + remaining itemized cables/fasteners; separately retain or replace other reservations exactly once','candidate_body_mass_kg':None,'whole_robot_updated':False,'inertia_update_required':'Subtract and add inertia expressed about common base origin, then recompute COM and inertia about new COM. Do not subtract tensors about different component COMs.'}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
