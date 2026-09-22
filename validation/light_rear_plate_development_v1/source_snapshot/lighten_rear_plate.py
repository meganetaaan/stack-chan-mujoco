"""Cut rounded interior windows while retaining rear-plate contact patches."""
import argparse
import hashlib
import json
from pathlib import Path
import cadquery as cq

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--out',type=Path,required=True)
a=p.parse_args()
root=Path(__file__).resolve().parents[3]
if a.out.exists():p.error('new output directory required')
a.out.mkdir(parents=True)
config=json.loads((root/'board/mechanical/engineering/rear_connection_candidate.json').read_text())
path=root/config['assets']['rear_plate']['path']
body_path=root/config['assets']['body']['path']
plate=cq.importers.importStep(str(path)).val()
body=cq.importers.importStep(str(body_path)).val()
windows=[{'y_min':-45,'y_max':45,'z_min':18,'z_max':44},
         {'y_min':-45,'y_max':45,'z_min':96,'z_max':110}]
plan=dict(scope=__doc__,windows_mm=windows,corner_radius_mm=3,
          criteria={'one_valid_solid':True,'contact_area_change_max_mm2':.001,'minimum_mass_saving_g':5},
          source_sha256={str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in (path,body_path)},
          limits=['Geometric screening only; structural stiffness, stress and buckling must be recomputed.',
                  'Preserved nominal contact does not establish bolt preload or load-path strength.'])
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
shape=plate
for w in windows:
 cutter=(cq.Workplane('YZ').rect(w['y_max']-w['y_min'],w['z_max']-w['z_min']).extrude(6)
         .edges('|X').fillet(3).val().translate((-66,(w['y_min']+w['y_max'])/2,(w['z_min']+w['z_max'])/2)))
 shape=shape.cut(cutter)
shape=shape.clean()
def contact_area(part, other, x):
 faces=lambda s:[f for f in s.Faces() if f.geomType()=='PLANE' and abs(f.BoundingBox().xmin-x)<1e-6 and abs(f.BoundingBox().xmax-x)<1e-6]
 return sum(f.intersect(g).Area() for f in faces(part) for g in faces(other))
contacts=[]
for name,other,x in [('body',body,-62.2)]+[(f'corner_washer_{i}',cq.importers.importStep(str(path.parent/f'corner_{i}_rear_washer.step')).val(),-64.2) for i in range(4)]:
 old=contact_area(plate,other,x);new=contact_area(shape,other,x)
 contacts.append(dict(name=name,old_area_mm2=old,new_area_mm2=new,passed=abs(new-old)<=.001))
# Yaw rear washers use the earlier staged envelope at a different x; compare projected contact by translating to the plate surface.
yaw=root/'validation/inset_yaw_assembly_development_v1/inset_fasteners_staged_v2'
for side in ('left','right'):
 for i in range(4):
  washer=cq.importers.importStep(str(yaw/f'{side}_{i}_rear_washer.step')).val()
  washer=washer.translate((-64.2-washer.BoundingBox().xmax,0,0))
  old=contact_area(plate,washer,-64.2);new=contact_area(shape,washer,-64.2)
  contacts.append(dict(name=f'{side}_yaw_washer_{i}',old_area_mm2=old,new_area_mm2=new,passed=abs(new-old)<=.001 and new>1))
saving=(plate.Volume()-shape.Volume())*2.7e-3
report=dict(old_mass_g=plate.Volume()*2.7e-3,new_mass_g=shape.Volume()*2.7e-3,saving_g=saving,
            contacts=contacts,gates=dict(one_valid_solid=shape.isValid() and len(shape.Solids())==1,
                                        contact_preserved=all(r['passed'] for r in contacts),mass_saving=saving>=5),
            structural_verified=False,manufacturing_release=False)
cq.exporters.export(shape,str(a.out/'rear_structural_plate.step'))
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
