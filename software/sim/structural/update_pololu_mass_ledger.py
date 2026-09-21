"""Replace obsolete power allocations, preserving uncertainty in the current mass ledger."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
import cadquery as cq
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();paths=[]
def read(p):
 p=Path(p);paths.append(p);return json.loads(p.read_text())
plan=read(a.out/'plan.json');basepath='validation/yaw_v7_payload_ledger_v1/report.json';base=read(basepath);power=read('schematics/power/dual_pololu_candidate.json');ms=read('docs/prototype/mechanical/pololu_mount_fasteners/candidate.json');rs=read('docs/prototype/mechanical/pololu_mount_fasteners/rear_candidate.json');inv=read('validation/pololu_mount_assembly_v1/inventory.json')['parts'];step=Path('validation/pololu_mount_assembly_v1/mount_assembly.step');paths.append(step);ss=cq.importers.importStep(str(step)).val().Solids();assert len(inv)==len(ss)==43
inherited={}
for group in ['retained_old_allocations','new_metal_parts','selected_SUS304_mount_washers','added_candidate_allocations']:
 for n,v in base[group].items():
  assert n not in inherited;inherited[n]={'mass_kg':v['mass_kg'],'basis':'Inherited comparison; see base ledger assumptions','origin_group':group}
assert abs(sum(x['mass_kg'] for x in inherited.values())-base['updated_fixed_terms']['mass_kg'])<1e-12
removed={n:inherited.pop(n) for n in ['UBEC_left','UBEC_right','rear_plate']};numeric={};density={};unknown={};coverage={}
for item,s in zip(inv,ss):
 n=item['name'];assert abs(s.Volume()-item['volume_mm3'])<1e-5
 if n=='rear_plate':
  mass=s.Volume()*2680e-9;basis='A5052P-H34 comparison density2680kg/m3 inherited, updated CAD with4 holes'
 elif item['group']=='spacer':mass=ms['spacer']['catalog_mass_g']/1000;basis='Selected spacer catalog nominal mass'
 elif item['group']=='module_hardware' and n.endswith('_screw'):mass=ms['screw']['catalog_mass_g']/1000;basis='Selected M2 screw catalog nominal mass'
 elif item['group']=='rear_hardware' and n.endswith('_screw'):mass=rs['screw']['mass_g']/1000;basis='Selected M3 screw catalog nominal mass'
 elif item['group']=='rear_hardware' and n.endswith('_nut'):mass=rs['nut']['mass_g']/1000;basis='Selected M3 nut catalog nominal mass'
 elif n.endswith('_bracket') or (item['group']=='rear_hardware' and n.endswith('_washer')):
  volume=s.Volume();c=np.asarray(s.Center().toTuple())*.001;unit_mass=volume*1e-9
  inertia=np.asarray(cq.Shape.matrixOfInertia(s))*1e-15
  origin=inertia+unit_mass*((c@c)*np.eye(3)-np.outer(c,c))
  density[n]={'mass_kg_per_kg_m3':unit_mass,'first_moment_kg_m_per_kg_m3':(unit_mass*c).tolist(),'inertia_origin_kg_m2_per_kg_m3':origin.tolist(),'basis':'Homogeneous material comparison only; printed infill/grade or washer alloy density unassigned','volume_mm3':volume};coverage[n]='density_coefficient';continue
 elif item['group']=='module_hardware' and n.endswith('_nut'):
  unknown[n]={'mass_kg':None,'reason':'Catalog mass unavailable; ideal hex collision solid must not be converted to mass'};coverage[n]='unknown';continue
 else:raise AssertionError(n)
 numeric[n]={'mass_kg':mass,'basis':basis,'part_number':item['part_number']};coverage[n]='numeric_comparison'
for side in ['left','right']:numeric['Pololu_'+side]={'mass_kg':power['catalog_mass_g_each']/1000,'basis':'Catalog nominal module mass; COM/inertia unknown','part_number':power['part']}
screw_reconciliation=read('validation/yaw_v7_screw_masses_v1/report.json')
yaw_inventory=Path('validation/yaw_integrated_candidate_v7/inventory.json');paths.append(yaw_inventory)
assert screw_reconciliation['source_sha256'][str(yaw_inventory)]==hashlib.sha256(yaw_inventory.read_bytes()).hexdigest()
assert len(screw_reconciliation['rows'])==20
for row in screw_reconciliation['rows']:
 n=row['name'];assert n not in numeric and n not in inherited and row['inventory_unchanged_from_revA']
 numeric[n]={'mass_kg':row['catalog_nominal_mass_g']/1000,'basis':'Previously reconciled existing yaw screw mass, absent from base fixed subtotal','part_number':row['selected_candidate']}
existing_screw_addition=sum(row['catalog_nominal_mass_g'] for row in screw_reconciliation['rows'])/1000
assert abs(existing_screw_addition-screw_reconciliation['nominal_screw_total_g']/1000)<1e-12
subtotal=sum(v['mass_kg'] for v in inherited.values())+sum(v['mass_kg'] for v in numeric.values())
plate_delta=numeric['rear_plate']['mass_kg']-removed['rear_plate']['mass_kg'];expected=base['updated_fixed_terms']['mass_kg']-sum(removed[n]['mass_kg'] for n in ['UBEC_left','UBEC_right'])+2*power['catalog_mass_g_each']/1000+plate_delta+8*ms['screw']['catalog_mass_g']/1000+8*ms['spacer']['catalog_mass_g']/1000+4*rs['screw']['mass_g']/1000+4*rs['nut']['mass_g']/1000+existing_screw_addition
assert abs(subtotal-expected)<1e-12 and set(coverage)=={i['name'] for i in inv}
assert len(density)==10 and len(unknown)==8
r={'base_ledger':basepath,'removed_allocations':removed,'retained_numeric_allocations':inherited,'new_numeric_allocations':numeric,'new_density_coefficients_per_kg_m3':density,'new_unknown_masses':unknown,'mount_assembly_coverage':coverage,'retained_density_coefficients_per_kg_m3':base['homogeneous_density_coefficients_per_kg_m3'],'numeric_comparison_subtotal_kg':subtotal,'numeric_subtotal_delta_kg':subtotal-base['updated_fixed_terms']['mass_kg'],'rear_plate_mass_delta_kg':plate_delta,'new_brackets_total_volume_mm3':sum(v['volume_mm3'] for n,v in density.items() if n.endswith('_bracket')),'inherited_unresolved':[x for x in base['remaining'] if not x.startswith('20 screw mass/')],'existing_yaw_screw_mass_added_kg':existing_screw_addition,'additional_unresolved':['Existing20 yaw screw nominal masses now included, but COM/inertia remain unqualified','8 new M2 nuts, two printed brackets and8 washers need actual mass or qualified density','Pololu and new catalog fasteners need mass distribution/COM before full inertia update','Printed geometry coefficients require print structure assumptions; not all infill is homogeneous','Wiring, terminals, protection hardware, fixtures and insulation still not fully allocated'],'itemized_mass_reconciliation_pass':True,'whole_robot_mass_kg':None,'whole_robot_com_m':None,'whole_robot_inertia_kg_m2':None,'model_updated':False,'manufacturing_release':False,'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:r[k] for k in ['numeric_comparison_subtotal_kg','numeric_subtotal_delta_kg','rear_plate_mass_delta_kg','new_brackets_total_volume_mm3']},indent=2))
