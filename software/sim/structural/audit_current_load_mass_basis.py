"""Check whether frozen load mass assumptions can qualify current candidates."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'software/sim/actuator'))
from fixtures import full_body
OUT=ROOT/'validation/current_load_mass_basis_v1';OUT.mkdir(exist_ok=True)
paths=[ROOT/'validation/current_torso_mass_v2/report.json',ROOT/'validation/torso_print_conditions_v1/report.json',ROOT/'software/sim/mujoco/assets/r9_fast_turn_v1/models/scene.xml',ROOT/'software/sim/mujoco/assets/r9_fast_turn_v1/FROZEN_FILES.json',ROOT/'software/sim/actuator/fixtures.py',ROOT/'docs/prototype/LOAD_INTERFACE_ja.md']
ledger,printed=[json.loads(p.read_text()) for p in paths[:2]]
frozen=json.loads(paths[3].read_text());assert frozen['models/scene.xml']==hashlib.sha256(paths[2].read_bytes()).hexdigest()
# Ensure comparison sets do not overlap; this is not a complete mass assignment.
a={x['name'] for x in ledger['rows'] if x['mass_kg'] is not None};b={x['name'] for x in printed['parts']};assert not a&b and len(a)==78 and len(b)==7
current={x['name']:x for x in ledger['rows']}
for row in printed['parts']:
 assert abs(current[row['name']]['material_volume_mm3']-row['material_volume_mm3'])<1e-6
sim,names=full_body();base=float(sim.m.body_mass[sim.m.body('base').id]);total=float(sim.m.body_mass.sum())
partial=ledger['numeric_comparison_subtotal_kg']+printed['homogeneous_printed_comparison_subtotal_kg']
result={'frozen_XML_hash_verified':True,'fixture_runtime_base_mass_kg':base,'fixture_runtime_whole_mass_kg':total,'current_numeric_and_homogeneous_printed_partial_kg':partial,'partial_compared_to_old_base_ratio':partial/base,'partial_minus_old_base_kg':partial-base,'component_counts':{'numeric':len(a),'homogeneous_print_comparison':len(b),'unassigned_CAD_parts':115-len(a)-len(b)},'exact_like_for_like_mass_comparison':False,'current_partial_is_guaranteed_lower_bound':False,'old_mass_sensitivity_fraction_documented':.05,'within_old_base_plus5percent_numeric_comparison':partial<=base*1.05,'frozen_loads_qualify_current_design':False,'reason':'Changed geometry, incomplete mass/COM/inertia and different component coverage; old uniform mass sensitivity does not cover local redistribution. Recompute after integration; no force/current scaling claim.','trace_provenance_limit':'EPIC4 trace reports name joints/settings but do not embed complete historical runtime body-mass array; current frozen fixture initialization is verified, not reconstructed historical execution','next_required':['Finish whole-body mass/COM/inertia and model-frame transforms','Preserve EPIC4 traces as historical comparisons','Build separate integrated model with current geometry and inertias','Export simultaneous loads through same structural/electrical interface, retaining failures and tolerances'],'model_modified':False,'physics_rerun':False,'manufacturing_release':False,'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
(OUT/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['fixture_runtime_base_mass_kg','current_numeric_and_homogeneous_printed_partial_kg','partial_compared_to_old_base_ratio']}))
