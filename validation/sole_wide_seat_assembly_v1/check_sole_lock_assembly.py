"""Sample assembly sequence for separate-spacer keyhole sole lock."""
import argparse,json,hashlib
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--cad-dir',type=Path);a=p.parse_args();root=Path(__file__).resolve().parents[3];a.out.mkdir(parents=True,exist_ok=False);src=(a.cad_dir or root/'validation/sole_separate_seat_lock_v1').resolve()
plan={'cad_directory':str(src),'scope':__doc__,'criteria':{'maximum_overlap_mm3':.01},'sequence':['Nut embedded before boot assembly','Insert sole with x offset 8 mm','Slide sole to final x','Insert separate spacer from below','Insert screw from below'], 'limitations':['Sampled nominal rigid geometry, not continuous path or tolerance proof.','Screw threads simplified; nut printing, tool engagement and tightening not qualified.']};(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');rows=[];hashes={}
for side in ['left','right']:
 objects={n:cq.importers.importStep(str(src/f'{side}_{n}.step')).val() for n in ['sole','yoke','spacer','screw','nut']};bootpath=root/f'validation/boot_low_head_candidate_v1/cad/{side}_boot_shell.step';objects['boot']=cq.importers.importStep(str(bootpath)).val()
 for f in [bootpath,*src.glob(f'{side}_*.step')]:hashes[str(f.relative_to(root))]=hashlib.sha256(f.read_bytes()).hexdigest()
 stages=[('sole_insert','sole',[(8,0,z) for z in [-8,-6,-4,-2,0]],['yoke','boot','nut']),('sole_slide','sole',[(x,0,0) for x in [8,6,4,2,0]],['yoke','boot','nut']),('spacer_insert','spacer',[(0,0,z) for z in [-8,-6,-4,-2,0]],['yoke','boot','nut','sole']),('screw_insert','screw',[(0,0,z) for z in [-10,-8,-6,-4,-2,0]],['yoke','boot','nut','sole','spacer'])]
 for stage,name,positions,fixed in stages:
  for pos in positions:
   moved=objects[name].translate(pos)
   for other in fixed:
    v=moved.intersect(objects[other]).Volume();rows.append({'side':side,'stage':stage,'moving':name,'fixed':other,'translation_mm':pos,'overlap_mm3':v,'passed':v<=.01})
r={'source_sha256':hashes,'checks':len(rows),'findings':[r for r in rows if not r['passed']],'rows':rows,'sampled_path_pass':all(r['passed'] for r in rows),'assembly_qualified':False};(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'checks':r['checks'],'findings':r['findings'],'sampled_path_pass':r['sampled_path_pass']},indent=2))
