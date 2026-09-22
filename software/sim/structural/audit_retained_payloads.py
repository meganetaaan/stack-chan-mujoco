"""Identify historical payload reservations that must be replaced before load release."""
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
source=Path('validation/yaw_inertial_ledger_v2/report.json');r=json.loads(source.read_text())
policy={
'Tab5':('retained_nominal','Check actual mounted accessories and datum; retain device nominal separately'),
'battery_2S_reservation':('replace_after_selection','Actual pack, BMS and location; do not add selected pack atop reservation'),
'dedicated_5V_converter':('replace_after_selection','Selected converter count, PCB and protection components; dual supplies are not covered by this single allocation'),
'TTL_interface':('replace_after_selection','Selected signal interface, PCB and location'),
'battery_tray':('process_and_geometry_pending','Selected pack fit and print process'),
'battery_strap_envelope':('hardware_pending','Exact retaining strap and routing'),
'left_yaw_motor_case':('assembly_boundary_pending','Reconcile catalog servo mass and geometric motor envelope without double counting'),
'right_yaw_motor_case':('assembly_boundary_pending','Reconcile catalog servo mass and geometric motor envelope without double counting'),
'left_battery_screw_envelope':('hardware_pending','Actual screw length and mass'),
'right_battery_screw_envelope':('hardware_pending','Actual screw length and mass')}
assert set(policy)==set(r['retained_old_allocations']), 'Review new/removed allocations'
rows=[dict(allocation=k,mass_kg=v['mass_kg'],status=policy[k][0],required_action=policy[k][1]) for k,v in r['retained_old_allocations'].items()]
result={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'rows':rows,'electrical_payload_reservations_to_replace_kg':sum(x['mass_kg'] for x in rows if x['status']=='replace_after_selection'),'rule':'Subtract each old mass, first moment and inertia before adding selected replacements; do not use mass-only delta for off-center payloads','complete_payload_qualified':False,'load_regeneration_allowed':False,'historical_model_changed':False}
(a.out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(result['electrical_payload_reservations_to_replace_kg'])
