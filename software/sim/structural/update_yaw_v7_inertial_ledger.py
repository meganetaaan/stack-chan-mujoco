"""Replace all existing yaw geometry allocations with v7 moments, retaining density unknowns."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
oldpath=Path('validation/yaw_inertial_ledger_v2/report.json');geompath=Path('validation/yaw_integrated_candidate_v7/geometric_moments.json');metalpath=Path('validation/yaw_metal_mass_v1/report.json')
old=json.loads(oldpath.read_text());geo={x['name']:x for x in json.loads(geompath.read_text())['parts']};rho={x['name']:x['density_reference_kg_m3'] for x in json.loads(metalpath.read_text())['parts']}
def terms(p,density):
 assert p['use_for_material_mass']
 m=p['mass_kg_per_density_kg_m3']*density;c=np.array(p['com_assembly_m']);I=np.array(p['inertia_com_kg_m2_per_density_kg_m3'])*density
 return {'mass_kg':m,'first_moment_kg_m':(m*c).tolist(),'inertia_origin_kg_m2':(I+m*((c@c)*np.eye(3)-np.outer(c,c))).tolist()}
def total(rows):return {k:np.sum([r[k] for r in rows],axis=0).tolist() for k in rows[0]}
metal={n:terms(geo[n],rho[n]) for n in old['new_metal_parts']};washers={n:terms(geo[n],7930) for n in old['selected_SUS304_mount_washers']};coeff={n:terms(geo[n],1) for n in old['homogeneous_density_coefficients_per_kg_m3']}
assert len(metal)==5 and len(washers)==8 and len(coeff)==11
fixed=total(list(old['retained_old_allocations'].values())+list(metal.values())+list(washers.values()))
changes=[]
for group,new in [('new_metal_parts',metal),('selected_SUS304_mount_washers',washers),('homogeneous_density_coefficients_per_kg_m3',coeff)]:
 for n,t in new.items():
  changes.append({'name':n,'group':group,'delta_terms':{k:(np.asarray(t[k])-np.asarray(old[group][n][k])).tolist() for k in t}})
assert not any('_nut' in n for n in set(metal)|set(washers)|set(coeff))
r={'source_sha256':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in [oldpath,geompath,metalpath]},'frame':old['frame'],'retained_old_allocations':old['retained_old_allocations'],'new_metal_parts':metal,'selected_SUS304_mount_washers':washers,'homogeneous_density_coefficients_per_kg_m3':coeff,'fixed_terms_including_retained_reservations':fixed,'replacements':changes,'replaced_geometry_allocations':24,'catalog_screw_mass_only_kg_unreconciled':old['catalog_screw_mass_only_kg'],'complete_base_mass_kg':None,'whole_robot_updated':False,'qualification':False,'unresolved':['11 density terms including body, supports and rear washers remain.','20 screw mass/position/shape allocations require reconciliation with v7; legacy sum retained as reference only.','8 nut masses remain unknown; collision-envelope density conversion forbidden.','Old battery/electronics/tray reservations retained explicitly; latest payload replacement still required.','Wiring and protection hardware must be itemized.','CAD frame must be transformed to model body frame before XML insertion.']}
(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'fixed_mass_kg':fixed['mass_kg'],'previous_fixed_mass_kg':old['fixed_terms_including_retained_reservations']['mass_kg'],'replaced':24,'density_terms':11},indent=2))
