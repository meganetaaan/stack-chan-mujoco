"""Build additive mass/first-moment/origin-inertia ledger, without inventing unknown masses."""
import argparse, hashlib, json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[3]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
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
fixed=combine(list(retained.values())+list(added.values()))
coefficients={v['name']:terms(v['mass_kg_per_density_kg_m3'],v['com_assembly_m'],v['inertia_com_kg_m2_per_density_kg_m3']) for v in geometry['parts'] if v['use_for_material_mass'] and v['name'] not in added}
assert len(added)==5 and len(coefficients)==19
report={'source_sha256':{x:hashlib.sha256((ROOT/x).read_bytes()).hexdigest() for x in paths},'frame':'base CAD origin; geometric assembly axes unchanged','old_origin_moment_reconstruction_max_errors':errors,'removed_old_allocations':sorted(excluded),'retained_old_allocations':retained,'new_metal_parts':added,'fixed_terms_including_retained_reservations':fixed,'homogeneous_density_coefficients_per_kg_m3':coefficients,'catalog_screw_mass_only_kg':hardware['catalog_nominal_total_g']/1000,'mass_subtotal_before_unknowns_kg':fixed['mass_kg']+hardware['catalog_nominal_total_g']/1000,'unresolved':['19 homogeneous solid density terms: 3 printed bodies and 16 washers; nonuniform print needs different moments','20 screws have catalog mass but no qualified COM/inertia','8 nuts have no selected mass/COM/inertia','Remaining wires and hardware formerly covered by 25g must be itemized','Retained battery/electronics/tray reservations still conditional; replace exactly once if changed'],'complete_base_mass_kg':None,'complete_base_inertia_kg_m2':None,'whole_robot_updated':False,'qualification':False}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'fixed_mass_kg':fixed['mass_kg'],'including_screw_mass_kg':report['mass_subtotal_before_unknowns_kg'],'density_terms':len(coefficients),'baseline_reconstruction_errors':errors},indent=2))
