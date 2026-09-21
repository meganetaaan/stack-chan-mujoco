"""Sample current holder insertion into existing boot/yoke before lock installation."""
import argparse,json,hashlib
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--holder-dir',type=Path,default=Path('validation/sole_contact_split_v1'));p.add_argument('--yoke-dir',type=Path,default=Path('validation/sole_external_nut_v1'));a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
rows=[];hashes={}
for side in ['left','right']:
 paths={'holder':a.holder_dir/f'{side}_holder_envelope.step','yoke':a.yoke_dir/f'{side}_yoke.step','boot':Path(f'validation/boot_low_head_candidate_v1/cad/{side}_boot_shell.step')}
 parts={k:cq.importers.importStep(str(v)).val() for k,v in paths.items()};hashes.update({str(v):hashlib.sha256(v.read_bytes()).hexdigest() for v in paths.values()})
 samples=[]
 for phase,positions in [('insert',[(8,-8+i*.5) for i in range(17)]),('slide',[(8-i*.5,0) for i in range(17)])]:
  for dx,dz in positions:
   moved=parts['holder'].translate((dx,0,dz));samples.append({'phase':phase,'dx_mm':dx,'dz_mm':dz,'overlap_mm3':{k:moved.intersect(parts[k]).Volume() for k in ['yoke','boot']}})
 rows.append({'side':side,'samples':samples,'sampled_nominal_overlap_free':all(v<1e-6 for s in samples for v in s['overlap_mm3'].values())})
r={'rows':rows,'source_sha256':hashes,'step_mm':.5,'manufacturing_release':False,'continuous_path_verified':False,'omitted':['Tolerances and deformation','Lock screw spacer and nut installed after alignment','Sheet adhesion and access','Hands and tools'],'scope':'Rigid nominal holder, sampled insertion and slide; no flexibility assumed'}
(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print([(r['side'],r['sampled_nominal_overlap_free'],max(v for s in r['samples'] for v in s['overlap_mm3'].values())) for r in rows])
