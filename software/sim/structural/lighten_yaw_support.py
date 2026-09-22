"""Remove rib-core material without changing nominal shelf or rear lands."""
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
source=root/'validation/inset_yaw_assembly_development_v1/yaw_inset_mount_v1'
plan=dict(scope=__doc__,triangle_xz_mm=[[-48,65],[-15,82],[-48,82]],corner_radius_mm=2,
          criteria={'single_valid_solid':True,'bounding_box_delta_max_mm':1e-6,
                    'shelf_and_rear_land_volume_change_max_mm3':1e-6,'minimum_mass_saving_per_support_g':2},
          density_assumed_kg_m3=1270,
          limitations=['Not strength or buckling approval','Only nominal geometry; no new physical load export'])
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
cutter=(cq.Workplane('XZ').polyline(plan['triangle_xz_mm']).close().extrude(120)
        .edges('|Y').fillet(2).val().translate((0,60,0)))
rows=[]
for side in ('left','right'):
 path=source/f'{side}_yaw_fixed_support.step'
 old=cq.importers.importStep(str(path)).val();new=old.cut(cutter).clean()
 removed=old.cut(new)
 # Entire shelf at z>=87 and rear wall at x<=-53.5 must be untouched.
 shelf=cq.Workplane('XY').box(200,200,30).val().translate((0,0,102))
 rear=cq.Workplane('XY').box(100,200,200).val().translate((-103.5,0,70))
 protected_loss=removed.intersect(shelf).Volume()+removed.intersect(rear).Volume()
 delta=max(abs(getattr(old.BoundingBox(),key)-getattr(new.BoundingBox(),key)) for key in ('xmin','xmax','ymin','ymax','zmin','zmax'))
 saving=(old.Volume()-new.Volume())*1.27e-3
 gates=dict(single_valid_solid=new.isValid() and len(new.Solids())==1,bbox=delta<=1e-6,protected_geometry=protected_loss<=1e-6,mass_saving=saving>=2)
 rows.append(dict(side=side,old_mass_g=old.Volume()*1.27e-3,new_mass_g=new.Volume()*1.27e-3,saving_g=saving,
                  protected_volume_loss_mm3=protected_loss,gates=gates,source_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
 cq.exporters.export(new,str(a.out/f'{side}_yaw_fixed_support.step'))
report=dict(rows=rows,geometry_screen_passed=all(all(r['gates'].values()) for r in rows),structural_verified=False)
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
