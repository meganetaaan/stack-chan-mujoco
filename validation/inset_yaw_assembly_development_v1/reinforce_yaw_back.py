"""Thicken yaw support back inward and enlarge rear lands; development geometry."""
import argparse,hashlib,json
from pathlib import Path
import cadquery as cq
ROOT=Path(__file__).resolve().parents[3]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
p.add_argument('--rib-thickness-mm',type=float,default=3.)
p.add_argument('--pattern-half-width-mm',type=float,default=9.)
a=p.parse_args()
if not 6<=a.pattern_half_width_mm<=9:p.error('pattern half-width must be between 6 and 9 mm')
if not 3<=a.rib_thickness_mm<=6:p.error('rib thickness must be between 3 and 6 mm')
a.out.mkdir(parents=True,exist_ok=False)
rows=[]
for side,sign in [('left',1),('right',-1)]:
 source=ROOT/'validation/yaw_connection_development_v1/yaw_connection_v1'/f'{side}_yaw_fixed_support.step'
 original=cq.importers.importStep(str(source)).val()
 # Back wall becomes 8 mm thick, x=-61.5..-53.5, within the old overall envelope.
 # Remove the old rear lands before placing the revised pattern.
 shape=original.cut(cq.Workplane('XY').box(.8,120,100).val().translate((-61.9,0,70)))
 shape=shape.fuse(cq.Workplane('XY').box(8,36,41.1).val().translate((-57.5,sign*26,70.45)))
 for dy in [-a.pattern_half_width_mm,a.pattern_half_width_mm]:
  for dz in [-12,12]:
   y,z=sign*26+dy,70+dz
   shape=shape.fuse(cq.Solid.makeCylinder(6,.7,cq.Vector(-62.2,y,z),cq.Vector(1,0,0)))
   shape=shape.cut(cq.Solid.makeCylinder(1.7,30,cq.Vector(-70,y,z),cq.Vector(1,0,0)))
 for y in [8,44-a.rib_thickness_mm]:
  rib=cq.Workplane('XZ').polyline([(-60,50.5),(10,88),(-60,88)]).close().extrude(a.rib_thickness_mm).val().translate((0,y+a.rib_thickness_mm,0))
  if sign<0:rib=rib.mirror('XZ')
  shape=shape.fuse(rib)
 shape=shape.clean();assert shape.isValid() and len(shape.Solids())==1
 b=shape.BoundingBox();old=original.BoundingBox()
 for axis in 'xyz':
  assert abs(getattr(b,axis+'min')-getattr(old,axis+'min'))<1e-6
  assert abs(getattr(b,axis+'max')-getattr(old,axis+'max'))<1e-6
 cq.exporters.export(shape,str(a.out/f'{side}_yaw_fixed_support.step'))
 rows.append(dict(side=side,volume_mm3=shape.Volume(),added_mass_kg=(shape.Volume()-original.Volume())*1.27e-6,
                  source_sha256=hashlib.sha256(source.read_bytes()).hexdigest()))
report=dict(scope=__doc__,rows=rows,pattern_half_width_mm=a.pattern_half_width_mm,back_thickness_mm=8,land_radius_mm=6,rib_thickness_mm=a.rib_thickness_mm,
            bolt_candidate_length_mm=20,nominal_stack_mm=13.9,remaining_thread_mm=6.1,
            limitations=['20 mm bolt envelopes and mating assembly not yet updated','no physical fastening/contact proof'],production_verified=False)
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
