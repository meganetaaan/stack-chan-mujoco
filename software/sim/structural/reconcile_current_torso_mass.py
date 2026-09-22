"""Reconcile every current torso solid without converting collision envelopes to mass."""
import argparse,hashlib,json
from pathlib import Path
import cadquery as cq
ROOT=Path(__file__).resolve().parents[3]
parser=argparse.ArgumentParser();parser.add_argument('--include-yaw-washer-mass',action='store_true');args=parser.parse_args()
OUT=ROOT/('validation/current_torso_mass_v2' if args.include_yaw_washer_mass else 'validation/current_torso_mass_v1');OUT.mkdir(exist_ok=True)
paths=[]
def read(name):
 p=ROOT/name;paths.append(p);return json.loads(p.read_text())
plan={'scope':'All115 current torso CAD entries, not whole robot','criteria':['Exactly one mass category per CAD entry','No old battery/tray/strap or shell silently carried forward','Unknown mass remains null; collision envelope is not material'], 'stop':'One reconciliation; no load simulation before unresolved allocations are assigned'}
(OUT/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
base=read('validation/pololu_mass_ledger_v2/report.json')
assembly=read('validation/serviceable_torso_v3/report.json')
washer=read('validation/rear_washer_clearance_v1/report.json') if args.include_yaw_washer_mass else None
frame=read('validation/tab5_frame_print_v1/report.json')
frame_screws=read('validation/tab5_frame_screws_v2/report.json')
paths.extend([ROOT/'docs/prototype/engineering/prototype_decision/PROTECTED_PACK_COMPARISON_ja.md',ROOT/'software/sim/structural/build_tab5_carrier_hardware_v2.py'])
step=ROOT/'validation/serviceable_torso_v3/assembly.step';paths.append(step)
solids=cq.importers.importStep(str(step)).val().Solids()
assert len(solids)==len(assembly['parts'])==115
numeric={**base['retained_numeric_allocations'],**base['new_numeric_allocations']}
density={**base['retained_density_coefficients_per_kg_m3'],**base['new_density_coefficients_per_kg_m3']}
alias={'Tab5':'Tab5','TTL':'TTL_interface','left_module_envelope':'Pololu_left','right_module_envelope':'Pololu_right'}
used=set();rows=[]
for item,solid in zip(assembly['parts'],solids):
 n=item['name'];assert abs(item['volume_mm3']-solid.Volume())<1e-5
 key=n.split('__',1)[-1] if '__' in n else alias.get(n)
 row={'name':n,'cad_volume_mm3':solid.Volume(),'mass_kg':None}
 if washer is not None and n.startswith('yaw__') and key in washer['parts']:
  old=washer['parts'][key];rho=washer['specification']['reference_density_kg_m3']
  assert abs(solid.Volume()*rho*1e-9-old['mass_kg'])<1e-12
  source=ROOT/f'validation/rear_washer_clearance_v1/{key}.step';paths.append(source)
  original=cq.importers.importStep(str(source)).val()
  assert solid.cut(original).Volume()+original.cut(solid).Volume()<1e-6
  row.update(category='qualified_geometry_comparison_mass',mass_kg=old['mass_kg'],basis='Custom SUS304 washer;7930kg/m3 reference density, proposed dimensions not supplier-certified',old_key=key)
 elif key in numeric:
  row.update(category='inherited_numeric_comparison',mass_kg=numeric[key]['mass_kg'],basis=numeric[key]['basis'],old_key=key);used.add(key)
 elif key in density or n in ('new_fixed_shell','new_carrier','new_tray'):
  volume=frame['volume_mm3'] if n=='new_carrier' else solid.Volume()
  row.update(category='unassigned_material_density',material_volume_mm3=volume,mass_coefficient_kg_per_kg_m3=volume*1e-9,basis='Homogeneous-material comparison only; actual print structure/grade unassigned')
  if n=='new_carrier':row['basis']+='; pre-insertion volume, not installed clearance subtraction: insertion redistributes polymer'
 elif n=='new_battery':row.update(category='catalog_nominal',mass_kg=.102,basis='ROBOTIS LB-020; protected pack comparison source; no mass tolerance/COM guarantee')
 elif n.startswith('new_frame_screw_'):row.update(category='catalog_nominal',mass_kg=frame_screws['candidate_added_mass_g']/4/1000,basis='NBK SLH-M3-8; frame screw report')
 elif n.startswith('new_') and n.endswith('_screw'):row.update(category='catalog_nominal',mass_kg=.0007,basis='NBK SLH-M3-10; previous side-hardware selection')
 else:row.update(category='unassigned_component_mass',basis='Selected insert/nut or strap envelope; actual mass unavailable, envelope-density conversion forbidden')
 rows.append(row)
assert len({r['name'] for r in rows})==115
excluded={k:v for k,v in numeric.items() if k not in used}
# These old allocations must not enter current CAD subtotal.
assert {'battery','tray','battery_strap_envelope'}<=excluded.keys()
subtotal=sum(r['mass_kg'] for r in rows if r['mass_kg'] is not None)
result={'rows':rows,'part_count':115,'category_counts':{c:sum(r['category']==c for r in rows) for c in sorted({r['category'] for r in rows})},'numeric_comparison_subtotal_kg':subtotal,'unmapped_old_numeric_allocations_excluded':excluded,'old_body_shroud_density_term_removed':True,'whole_robot_mass_kg':None,'whole_robot_com_m':None,'whole_robot_inertia_kg_m2':None,'model_updated':False,'manufacturing_release':False,'remaining':['Printed shell/frame/tray/support/bracket material and process allocation','Insert/nut/strap mass','Motor assemblies, complete articulated legs/feet absent from this torso scope','Protection/control PCBs, harnesses, connectors, insulation and fixtures absent','Part mass tolerances and internal distributions; CAD frame to MuJoCo transform','Latest integrated loads and deformed clearance not established'],'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
(OUT/'report.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ['part_count','category_counts','numeric_comparison_subtotal_kg','unmapped_old_numeric_allocations_excluded']},indent=2))
