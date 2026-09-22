"""Build additive mass/first-moment/origin-inertia ledger, without inventing unknown masses."""
import argparse, hashlib, json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[3]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--include-selected-washers',action='store_true');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
paths=['validation/base_mass_provenance_development_v1/report.json','validation/yaw_metal_mass_v1/report.json','validation/yaw_hardware_catalog_mass_v1/report.json','validation/yaw_geometric_moments_v1/geometric_moments.json']
old,metal,hardware,geometry=[json.loads((ROOT/x).read_text()) for x in paths]
for report in [old,metal]:
 for path,sha in report['source_sha256'].items():
  assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==sha, path
inventory=ROOT/'board/mechanical/prototype/yaw_support_candidate/revA/inventory.json'
assert hashlib.sha256(inventory.read_bytes()).hexdigest()==hardware['source_inventory_sha256']
def terms(m,c,i):
 c=np.array(c);i=np.array(i)
 return {'mass_kg':m,'first_moment_kg_m':(m*c).tolist(),'inertia_origin_kg_m2':(i+m*(np.dot(c,c)*np.eye(3)-np.outer(c,c))).tolist()}
def combine(rows):
 return {k:np.sum([r[k] for r in rows],axis=0).tolist() for k in rows[0]}
all_old=[terms(v['mass_kg'],v['com_base_m'],v['inertia_com_kg_m2']) for v in old['components'].values()]
aggregate=old['aggregate'];expected=terms(aggregate['mass_kg'],aggregate['com_m'],aggregate['inertia_kg_m2'])
reconstructed=combine(all_old)
errors={k:float(np.max(np.abs(np.asarray(reconstructed[k])-expected[k]))) for k in expected}
assert max(errors.values())<1e-12
excluded={'body_shroud','rear_cover','left_yaw_fixed_support','right_yaw_fixed_support','cables_and_fasteners'}
retained={n:terms(v['mass_kg'],v['com_base_m'],v['inertia_com_kg_m2']) for n,v in old['components'].items() if n not in excluded}
added={v['name']:terms(v['mass_kg'],v['com_assembly_m'],v['inertia_com_kg_m2']) for v in metal['parts']}
washer_rows={}
if a.include_selected_washers:
 spec_path='docs/prototype/mechanical/sole_spacer/specification.json'
 spec=json.loads((ROOT/spec_path).read_text());paths.append(spec_path)
 assert spec['part_number']=='SCW-SOLE-SPACER-01' and spec['material_requirement'].startswith('SUS304')
 rho=next(x['density_reference_kg_m3'] for x in metal['parts'] if x['material_candidate']=='SUS304')
 for v in geometry['parts']:
  if '_plate_' not in v['name'] or not v['name'].endswith('_washer'):continue
  assert v['use_for_material_mass']
  nominal_volume=np.pi/4*(spec['outer_diameter']['nominal']**2-spec['inner_diameter']['nominal']**2)*spec['thickness']['nominal']
  assert abs(v['volume_mm3']-nominal_volume)<1e-6
  washer_rows[v['name']]=terms(v['mass_kg_per_density_kg_m3']*rho,v['com_assembly_m'],np.array(v['inertia_com_kg_m2_per_density_kg_m3'])*rho)
 assert len(washer_rows)==spec['quantity_breakdown']['yaw_mount_plates']==8
fixed=combine(list(retained.values())+list(added.values())+list(washer_rows.values()))
coefficients={v['name']:terms(v['mass_kg_per_density_kg_m3'],v['com_assembly_m'],v['inertia_com_kg_m2_per_density_kg_m3']) for v in geometry['parts'] if v['use_for_material_mass'] and v['name'] not in added and v['name'] not in washer_rows}
assert len(added)==5 and len(coefficients)==19-len(washer_rows)
report={'source_sha256':{x:hashlib.sha256((ROOT/x).read_bytes()).hexdigest() for x in paths},'frame':'base CAD origin; geometric assembly axes unchanged','old_origin_moment_reconstruction_max_errors':errors,'removed_old_allocations':sorted(excluded),'retained_old_allocations':retained,'new_metal_parts':added,'selected_SUS304_mount_washers':washer_rows,'fixed_terms_including_retained_reservations':fixed,'homogeneous_density_coefficients_per_kg_m3':coefficients,'catalog_screw_mass_only_kg':hardware['catalog_nominal_total_g']/1000,'mass_subtotal_before_unknowns_kg':fixed['mass_kg']+hardware['catalog_nominal_total_g']/1000,'unresolved':[f'{len(coefficients)} homogeneous solid density terms remain; nonuniform print needs different moments','20 screws have catalog mass but no qualified COM/inertia','8 nuts have no selected mass/COM/inertia','Remaining wires and hardware formerly covered by 25g must be itemized','Retained battery/electronics/tray reservations still conditional; replace exactly once if changed'],'complete_base_mass_kg':None,'complete_base_inertia_kg_m2':None,'whole_robot_updated':False,'qualification':False}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'fixed_mass_kg':fixed['mass_kg'],'including_screw_mass_kg':report['mass_subtotal_before_unknowns_kg'],'density_terms':len(coefficients),'baseline_reconstruction_errors':errors},indent=2))
