"""Keyhole yoke variant for rigid insertion of existing TPU mushroom heads."""
import argparse,json,hashlib
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();root=Path(__file__).resolve().parents[3];a.out.mkdir(parents=True,exist_ok=False)
plan={'scope':__doc__,'insertion_offset_x_mm':8,'entry_radius_mm':4.2,'slot_radius_mm':3,'criteria':{'single_valid_yoke':True,'sampled_overlap_max_mm3':.01},'limitations':['Sliding lock absent: concept must not be released as retained assembly.','Sampled insertion only, not continuous tolerance/deformation certification.','Enlarged openings require yoke strength reanalysis.']};(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');rows=[]
for side,cy in [('left',6),('right',-6)]:
 source=root/f'validation/sole_retention_concept_v1/{side}_foot_yoke.step';yoke=cq.importers.importStep(str(source)).val();sole=cq.importers.importStep(str(root/f'validation/sole_retention_concept_v1/{side}_sole_TPU.step')).val();boot=cq.importers.importStep(str(root/f'validation/boot_low_head_candidate_v1/cad/{side}_boot_shell.step')).val();before=yoke.Volume()
 for x in [-16,24]:
  for y in [cy-16,cy+16]:
   entry=cq.Solid.makeCylinder(4.2,3.02,cq.Vector(x+8,y,-19.01));slot=cq.Solid.makeBox(8,6,3.02,cq.Vector(x,y-3,-19.01));yoke=yoke.cut(entry.fuse(slot))
 yoke=yoke.clean();cq.exporters.export(yoke,str(a.out/f'{side}_foot_yoke.step'));samples=[]
 for phase,offsets in [('insert',[(8,z) for z in [-8,-6,-4,-2,0]]),('slide',[(x,0) for x in [8,6,4,2,0]])]:
  for dx,dz in offsets:
   moved=sole.translate((dx,0,dz));samples.append({'phase':phase,'translation_mm':[dx,0,dz],'yoke_overlap_mm3':moved.intersect(yoke).Volume(),'boot_overlap_mm3':moved.intersect(boot).Volume()})
 rows.append({'side':side,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'valid_single_solid':yoke.isValid() and len(yoke.Solids())==1,'removed_volume_mm3':before-yoke.Volume(),'samples':samples,'sampled_path_pass':all(max(s['yoke_overlap_mm3'],s['boot_overlap_mm3'])<=.01 for s in samples)})
r={'rows':rows,'retention_verified':False,'anti_slide_lock_designed':False};(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
