"""Map seven printed current torso parts to an explicit comparison process."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'validation/torso_print_conditions_v1';OUT.mkdir(exist_ok=True)
files=[ROOT/'validation/current_torso_mass_v1/report.json',ROOT/'board/mechanical/prototype/rc_battery_tray_revB/material_candidate.json',ROOT/'board/mechanical/engineering/materials.json']
ledger,material,screen=[json.loads(p.read_text()) for p in files]
names={'yaw__left_yaw_fixed_support','yaw__right_yaw_fixed_support','power__left_bracket','power__right_bracket','new_fixed_shell','new_carrier','new_tray'}
rows=[];washers=[]
for r in ledger['rows']:
 if r['category']!='unassigned_material_density':continue
 if r['name'] not in names:
  assert 'washer' in r['name'];washers.append(r['name']);continue
 rows.append({'name':r['name'],'material_volume_mm3':r['material_volume_mm3'],'comparison_density_kg_m3':material['typical_density_g_cm3']*1000,'homogeneous_comparison_mass_kg':r['material_volume_mm3']*material['typical_density_g_cm3']*1e-6,'manufactured_mass_kg':None,'build_orientation':None,'allowed_stress_MPa':None,'process_released':False})
assert {r['name'] for r in rows}==names and len(washers)==16
result={'scope':'Seven printed solids from115-part torso; feet/other leg parts excluded','candidate_material':material['product'],'comparison_process':material['print_starting_conditions'],'process_source_is_legacy_comparison_not_validated_for_new_parts':True,'parts':rows,'metal_washers_excluded_from_print_material':washers,'homogeneous_printed_comparison_subtotal_kg':sum(r['homogeneous_comparison_mass_kg'] for r in rows),'actual_printed_subtotal_kg':None,'legacy_FE_allowable_screen_MPa':screen['PETG']['nominal_allowable_MPa'],'legacy_FE_allowable_is_qualified_for_manufacturing':False,'design_choices':['Use existing standard PETG candidate for first common material comparison; ABS alternative remains','No TPU assignment to these load-bearing torso supports; TPU remains a contact/cushion candidate','Use pre-insertion carrier volume; installed approximation is not lost polymer'],'required_process_inputs':['Printer/nozzle and actual material product','Orientation for each part and load direction relative to layers','Wall/perimeter, solid-fill path, support removal and hole finishing','Insert installation temperature/depth, torque and retained preload','Finished dimensions and retention/creep acceptance tied to loads'],'manufacturing_release':False,'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
(OUT/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'printed_parts':len(rows),'metal_washers':len(washers),'homogeneous_comparison_kg':result['homogeneous_printed_comparison_subtotal_kg']}))
