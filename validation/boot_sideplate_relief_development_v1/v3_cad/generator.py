"""Cut a local boot opening for the raised ankle bridge; preserve sole and mounting lugs."""
import argparse,hashlib,json
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[3]
if a.out.exists():p.error('new output required')
a.out.mkdir(parents=True)
paths=[root/f'software/sim/mujoco/assets/r9_fast_turn_v1/cad/{s}_boot_shell.step' for s in ('left','right')]
plan={'opening_roll_frame_mm':{'x':[-31.5,3],'y':[-32,32],'z':[15,45]},'criteria':{'valid_single_solid':True,'unchanged_below_z_mm':10},'source_sha256':{str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in paths},'limitations':['Candidate opening only; edge radii, boot stiffness and whole assembly clearance remain unverified.']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');rows=[]
cut=cq.Workplane('XY').box(34.5,64,30).val().translate((-14.25,0,30))
protected=cq.Workplane('XY').box(200,200,200).val().translate((0,0,-90))
for side,path in zip(('left','right'),paths):
 old=cq.importers.importStep(str(path)).val();new=old.cut(cut).clean()
 row={'side':side,'valid_single_solid':new.isValid() and len(new.Solids())==1,'removed_volume_mm3':old.Volume()-new.Volume(),'protected_region_removed_mm3':old.intersect(protected).Volume()-new.intersect(protected).Volume()}
 rows.append(row);cq.exporters.export(new,str(a.out/f'{side}_boot_shell.step'))
(a.out/'report.json').write_text(json.dumps({'rows':rows,'manufacturing_release':False},indent=2)+'\n');print(json.dumps(rows))
