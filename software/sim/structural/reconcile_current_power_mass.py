"""Compare mount ledgers and expose circuit references not mass-reconciled."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
oldp=ROOT/'validation/pololu_mass_ledger_v1/report.json';newp=ROOT/'validation/pololu_mass_ledger_v2/report.json';ep=ROOT/'schematics/power/system_power_integration_candidate_v1/assembly.json'
old,new,e=[json.loads(p.read_text()) for p in [oldp,newp,ep]]
assert old['numeric_comparison_subtotal_kg']==new['numeric_comparison_subtotal_kg']
assert old['new_numeric_allocations']==new['new_numeric_allocations']
assert old['new_unknown_masses']==new['new_unknown_masses']
deltas={}
for name,v in new['new_density_coefficients_per_kg_m3'].items():
 ov=old['new_density_coefficients_per_kg_m3'][name]
 if not name.endswith('_bracket'):
  assert v==ov
  continue
 deltas[name]={'volume_delta_mm3':v['volume_mm3']-ov['volume_mm3'],
  'mass_delta_kg_per_kg_m3':v['mass_kg_per_kg_m3']-ov['mass_kg_per_kg_m3'],
  'first_moment_delta_kg_m_per_kg_m3':[a-b for a,b in zip(v['first_moment_kg_m_per_kg_m3'],ov['first_moment_kg_m_per_kg_m3'])],
  'inertia_origin_delta_kg_m2_per_kg_m3':[[a-b for a,b in zip(row,orow)] for row,orow in zip(v['inertia_origin_kg_m2_per_kg_m3'],ov['inertia_origin_kg_m2_per_kg_m3'])]}
mapping={'SYS__LEFT_U_REGULATOR':'Pololu_left','SYS__RIGHT_U_REGULATOR':'Pololu_right'}
rows=[]
for part in e['parts']:
 ref=part['reference'];entry=mapping.get(ref)
 if entry:
  assert new['new_numeric_allocations'][entry]['part_number']==part['part']
 rows.append({'reference':ref,'part':part.get('part'),'ledger_entry':entry,
 'status':'catalog_mass_only_COM_inertia_unqualified' if entry else 'not_reconciled_to_current_mass_ledger'})
r={'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [oldp,newp,ep]},
 'bracket_coefficient_deltas':deltas,'numeric_subtotal_unchanged':True,
 'circuit_mass_reconciliation':rows,'circuit_references':len(rows),'mapped_catalog_mass_references':len(mapping),
 'unreconciled_references':len(rows)-len(mapping),
 'interpretation':'Unreconciled does not mean zero mass or necessarily all new mass: reconcile existing TTL/board reservations before adding allocations. PCB substrate, copper, solder, wiring and connectors require explicit boundaries to avoid double counting.',
 'whole_robot_mass_kg':None,'model_updated':False,'manufacturing_release':False}
(newp.parent/'reconciliation.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps({'bracket_volume_delta_mm3':sum(v['volume_delta_mm3'] for v in deltas.values()),'circuit_references':len(rows),'unreconciled':r['unreconciled_references']}))
