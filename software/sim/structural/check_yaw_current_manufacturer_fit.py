"""Screen manufacturer servo details against fixed yaw assembly at nominal placement."""
import argparse,hashlib,json
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--step',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
reference=Path('validation/servo_reference_geometry_v1/report.json');ref=json.loads(reference.read_text())
assert hashlib.sha256(a.step.read_bytes()).hexdigest()==ref['source_sha256']
pointer=Path('board/mechanical/prototype/yaw_support_candidate/current.json');ptr=json.loads(pointer.read_text());assembly=Path(ptr['assembly'])
a.out.mkdir(parents=True,exist_ok=False)
plan={'criterion':'Flag overlap volume > 0.01 mm3; zero overlap is not full fit qualification.',
 'placement':'Proper rotation (x,y,z)->(y,x,-z), translation (-5,+/-26,68.5) mm. Chosen to match model case box and horn outer face at yaw pivot z=62.',
 'assumptions':['Native horn outer face z=6.5 is taken as joint plane; shaft axial datum needs confirmation.','Same front/back orientation for both yaw motors.'],
 'limitations':['Reference STEP has no manufacturing tolerances.','Rear idler group is screened separately; inclusion in build not established.','No mating cable housing or servo fasteners added.','This tests fixed parts only, not moving coupler.']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
solids=cq.importers.importStep(str(a.step)).val().Solids();fixed=cq.importers.importStep(str(assembly)).val()
rows=[]
for side,cy in [('left',26),('right',-26)]:
 placed=[s.rotate((0,0,0),(1,1,0),180).translate((-5,cy,68.5)) for s in solids]
 case=cq.Compound.makeCompound(placed[:3]);b=case.BoundingBox()
 actual=[b.xmin,b.ymin,b.zmin,b.xmax,b.ymax,b.zmax];expected=[-29.5,cy-10,65,4.5,cy+10,88]
 assert max(abs(x-y) for x,y in zip(actual,expected))<1e-5
 for name,ids in [('case',[0,1,2]),('connectors',[13,14]),('rear_idler',[10,11,12])]:
  shape=cq.Compound.makeCompound([placed[i] for i in ids]);overlap=shape.intersect(fixed).Volume()
  rows.append({'side':side,'group':name,'solid_indices':ids,'overlap_mm3':overlap,'flagged':overlap>.01,'distance_mm':shape.distance(fixed)})
report={'source_sha256':{str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in [reference,pointer,assembly]},
 'manufacturer_step_sha256':ref['source_sha256'],'case_box_alignment_verified':True,'rows':rows,
 'full_fit_qualified':False,'manufacturing_release':False}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(rows))
