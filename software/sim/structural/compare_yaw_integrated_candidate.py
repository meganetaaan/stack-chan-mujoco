"""Account for integrated comparison changes without double-counting old parts."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate',type=Path,required=True);a=p.parse_args()
base=Path('board/mechanical/prototype/yaw_support_candidate/revB');hashes={}
def read(folder,name):
 path=folder/name;hashes[str(path)]=hashlib.sha256(path.read_bytes()).hexdigest();return json.loads(path.read_text())
old={r['name']:r for r in read(base,'inventory.json')['parts']};new={r['name']:r for r in read(a.candidate,'inventory.json')['parts']}
om={r['name']:r for r in read(base,'geometric_moments.json')['parts']};nm={r['name']:r for r in read(a.candidate,'geometric_moments.json')['parts']}
assert old.keys()==new.keys() and len(old)==52
changed=[];unchanged=[];mass_delta=0.;first_delta=np.zeros(3);I_delta=np.zeros((3,3))
for name in old:
 expected=name.endswith(('yaw_fixed_support','mount_plate')) or ('_plate_' in name and name.endswith('_washer'))
 dv=new[name]['volume_mm3']-old[name]['volume_mm3']
 if not expected:
  assert abs(dv)<1e-7 and old[name]['source']==new[name]['source'] and old[name].get('source_sha256')==new[name].get('source_sha256')
  assert np.allclose(om[name]['com_assembly_m'],nm[name]['com_assembly_m'],atol=1e-12,rtol=0)
  assert np.allclose(om[name]['inertia_com_kg_m2_per_density_kg_m3'],nm[name]['inertia_com_kg_m2_per_density_kg_m3'],atol=1e-18,rtol=1e-8)
  unchanged.append(name);continue
 rho=1270 if name.endswith('yaw_fixed_support') else 7930
 delta=0.
 for sign,part in [(-1,om[name]),(1,nm[name])]:
  m=part['mass_kg_per_density_kg_m3']*rho;c=np.array(part['com_assembly_m']);I=np.array(part['inertia_com_kg_m2_per_density_kg_m3'])*rho
  delta+=sign*m;first_delta+=sign*m*c;I_delta+=sign*(I+m*(np.dot(c,c)*np.eye(3)-np.outer(c,c)))
 mass_delta+=delta
 changed.append({'name':name,'volume_delta_mm3':dv,'assumed_density_kg_m3':rho,'mass_delta_g':delta*1000})
assert len(changed)==12 and len(unchanged)==40
result={'source_sha256':hashes,'changed_parts':changed,'unchanged_names':unchanged,'delta_mass_g':mass_delta*1000,'delta_first_moment_kg_m':first_delta.tolist(),'delta_inertia_about_assembly_origin_kg_m2':I_delta.tolist(),
 'limits':['Replacement deltas, not additions to old parts twice.','Uniform solid PETG 1270 and SUS304 7930 kg/m3 are comparison inputs, not guaranteed actual masses.','Origin inertia delta is not a centre-of-mass tensor and need not be positive definite.','No complete body/robot mass or load update; electronics and harness still separate.'],'current_pointer_updated':False,'manufacturing_release':False}
(a.candidate/'change_accounting.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'changed':len(changed),'unchanged':len(unchanged),'delta_mass_g':result['delta_mass_g']}))
