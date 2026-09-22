"""Distinguish retained mass placeholders from genuinely unallocated harness items."""
import argparse, csv, hashlib, json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
paths=[Path(x) for x in ['validation/yaw_inertial_ledger_v2/report.json','validation/payload_inertial_replacement_v1/report.json','schematics/power/split_servo_harness_revA/connections.csv','validation/base_mass_bounds_v1/report.json']]
yaw=json.loads(paths[0].read_text());replacement=json.loads(paths[1].read_text())
assert replacement['sources_sha256'][str(paths[0])]==hashlib.sha256(paths[0].read_bytes()).hexdigest()
retained={k:v for k,v in yaw['retained_old_allocations'].items() if k not in replacement['removed_old_allocations']}
rows=[]
for name,v in retained.items():
 rows.append({'item':name,'accounting':'already_in_partial_base_subtotal','mass_kg':v['mass_kg'],'action':'Replace mass, first moment and inertia together after selection; do not add a second allocation.'})
connections=list(csv.DictReader(paths[2].open()))
assert len(connections)==36 and len({(x['connector'],x['pin']) for x in connections})==36
harness=[{'joint':x['joint'],'connector':x['connector'],'pin':x['pin'],'net':x['net'],
 'wire_status':x['wire_status'],'route_length_m':None,'mass_kg':None,
 'body_allocation':None} for x in connections]
report={'source_sha256':{str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in paths},
 'retained_allocations':rows,'added_payload_names':list(replacement['added_candidate_allocations']),
 'unallocated_servo_conductors':harness,
 'other_unallocated':['Servo connector housings and crimps','Battery/distribution/Tab5/USB cabling and strain relief','Protection PCB and fitted parts not included in UBEC modules'],
 'rules':['TTL interface and battery strap are already represented by historical placeholders, not zero-mass omissions.',
 'Wire lengths from the stationary jig are not dynamic robot routing lengths.',
 'Moving harness mass must be assigned across actual attached bodies; do not put all 36 conductors in the base.',
 'Preserve the removal of the old 25 g cables-and-fasteners reservation; replace with itemized allocations.'],
 'whole_base_complete':False,'robot_mass_complete':False,'model_updated':False}
a.out.mkdir(parents=True,exist_ok=False);(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'retained_count':len(rows),'retained_mass_kg':sum(x['mass_kg'] for x in rows),'unallocated_conductors':len(harness)}))
