"""Create provisional embedded-nut cavities and sole screw-head recesses."""
import argparse,hashlib,json
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[3]
if a.out.exists():p.error('new output required')
a.out.mkdir(parents=True)
paths={s:{'boot':root/f'validation/boot_seats_development_v1/{s}_boot_shell.step','sole':root/f'software/sim/mujoco/assets/r9_fast_turn_v1/cad/{s}_sole_TPU.step'} for s in ('left','right')}
plan={'scope':__doc__,'provisional_nut_cavity_mm':[4.4,4.4,1.8],'nut_cavity_z_mm':[-14.6,-12.8],'sole_head_recess_radius_mm':2.3,'sole_head_recess_z_mm':[-21.2,-19],'criteria':{'single_valid_solid':True,'floor_nominal_min_mm':.8},'assembly_hypothesis':'Insert nuts during boot print pause; attach boot to yoke from below with sole removed; install removable sole afterward.','source_sha256':{str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for row in paths.values() for f in row.values()},'limitations':['No purchased nut or screw selected; cavity is provisional, not a standardized fastener specification.','Print pause, nut insertion, roof closure, sole retention, preload and strength unqualified.']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');rows=[]
for side,files in paths.items():
 shapes={k:cq.importers.importStep(str(v)).val() for k,v in files.items()};original=shapes.copy();sign=1 if side=='left' else -1
 for x in (-34,36):
  for y in (sign*6-20.5,sign*6+20.5):
   cavity=cq.Workplane('XY').box(4.4,4.4,1.8).val().translate((x,y,-13.7))
   shapes['boot']=shapes['boot'].cut(cavity)
   pocket=cq.Solid.makeCylinder(2.3,2.21,cq.Vector(x,y,-21.2))
   shapes['sole']=shapes['sole'].cut(pocket)
 for part,shape in shapes.items():
  shape=shape.clean();valid=shape.isValid() and len(shape.Solids())==1
  rows.append({'side':side,'part':part,'valid_single_solid':valid,'removed_volume_mm3':original[part].Volume()-shape.Volume()})
  cq.exporters.export(shape,str(a.out/f'{side}_{"boot_shell" if part=="boot" else "sole_TPU"}.step'))
(a.out/'report.json').write_text(json.dumps({'rows':rows,'geometry_only_pass':all(x['valid_single_solid'] for x in rows),'manufacturing_release':False},indent=2)+'\n');print(json.dumps(rows,indent=2))
