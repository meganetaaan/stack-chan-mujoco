"""Transfer a rigid clearance lower bound only after CAD set-inclusion checks."""
import argparse,hashlib,json
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
base=Path('validation/yaw_integrated_candidate_v6');new=Path('validation/yaw_integrated_candidate_v7');prior=Path('validation/yaw_integrated_motion_v6/report.json');files=[prior];parts={}
plan={'question':'Is every v7 fixed solid contained in its v6 counterpart so that removing material cannot decrease rigid moving-to-fixed distance?', 'method':'Check unchanged inventory and bidirectional CAD differences for50parts; positive-volume CAD difference new minus old for2supports; confirm each prior fixed-assembly hash.', 'cad_volume_tolerance_mm3':1e-6,'stop':'One subset check; no new angle sampling or geometry changes.','limits':['Numerical B-rep set comparison, not formal exact-arithmetic proof.','Only original yaw coupler/cradle moving group and fixed assembly.','Deformation/tolerance allowances remain separate requirements; stronger flex cannot be ruled out by set inclusion.']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
for label,folder in [('old',base),('new',new)]:
 ip=folder/'inventory.json';sp=folder/'yaw_support_candidate.step';files += [ip,sp];inv=json.loads(ip.read_text())['parts'];solids=cq.importers.importStep(str(sp)).val().Solids();assert len(solids)==len(inv)==52
 parts[label]={}
 for item,s in zip(inv,solids):
  assert abs(item['volume_mm3']-s.Volume())<1e-5
  parts[label][item['name']]=(item,s)
assert parts['old'].keys()==parts['new'].keys();checks=[]
for n,(item,s) in parts['new'].items():
 oi,old=parts['old'][n]
 if n in ['left_yaw_fixed_support','right_yaw_fixed_support']:
  outside=s.cut(old).Volume();removed=old.cut(s).Volume();assert outside<1e-6 and removed>0
  checks.append({'name':n,'new_material_outside_old_mm3':outside,'removed_volume_mm3':removed})
 else:
  assert item==oi
  assert s.cut(old).Volume()<1e-6 and old.cut(s).Volume()<1e-6
r=json.loads(prior.read_text());assert r['passed_screen']
for row in r['results']:
 for f,sha in row['cad_sha256'].items():assert hashlib.sha256(Path(f).read_bytes()).hexdigest()==sha
result={'subset_checks':checks,'unchanged_parts':50,'inherited_rigid_clearance':[{k:row[k] for k in ['side','angle_range_rad','minimum_sampled_distance_mm','sampling_miss_bound_mm','residual_lower_bound_mm','passed_screen']} for row in r['results']],'interpretation':'Listed bounds from v6 remain conservative for the rigid v7 geometry; not newly measured v7 minima.','source_sha256':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},'full_assembly_verified':False,'manufacturing_release':False}
(a.out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'subset_checks':checks,'unchanged':50,'inherited_minimum_residual_lower_bound_mm':min(x['residual_lower_bound_mm'] for x in r['results'])},indent=2))
