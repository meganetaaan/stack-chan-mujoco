"""Update pre-insertion carrier and prove consistency with installed-envelope candidate."""
import hashlib,json
from pathlib import Path
import cadquery as cq
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'validation/tab5_frame_print_v1';OUT.mkdir(exist_ok=True)
source=ROOT/'validation/tab5_insert_candidate_v1/carrier_print.step'
reference=ROOT/'validation/tab5_frame_screws_v2/carrier_installed_approximation.step'
plan_path=ROOT/'validation/tab5_frame_screws_v2/plan.json';plan=json.loads(plan_path.read_text())
shape=cq.importers.importStep(str(source)).val();original_volume=shape.Volume()
for y in [-60,60]:
 for z in [52,124]:
  start,end=plan['recess_x_mm'];shape=shape.cut(cq.Solid.makeCylinder(plan['head_recess_diameter_mm']/2,end-start,cq.Vector(start,y,z),cq.Vector(1,0,0)))
shape=shape.clean();assert shape.isValid() and len(shape.Solids())==1
approx=shape
for sign in [-1,1]:
 for z in [88,112]:
  approx=approx.cut(cq.Solid.makeCylinder(2.3,5.7,cq.Vector(42,sign*55,z),cq.Vector(0,sign,0)))
target=cq.importers.importStep(str(reference)).val()
difference=approx.cut(target).Volume()+target.cut(approx).Volume();assert difference<1e-6
cq.exporters.export(shape,str(OUT/'carrier_print.step'))
result={'valid':shape.isValid(),'solids':len(shape.Solids()),'volume_mm3':shape.Volume(),'removed_volume_mm3':original_volume-shape.Volume(),
 'installed_approximation_symmetric_difference_mm3':difference,'manufacturing_release':False,
 'not_qualified':['Thread engagement in Tab5','Printed hole compensation and insert retention','Recess bearing strength and assembly torque','Print orientation/process/material allowables'],
 'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [source,reference,plan_path]}}
(OUT/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
