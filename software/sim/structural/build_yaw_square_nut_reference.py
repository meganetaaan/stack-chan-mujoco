"""Square nut reference solids for bearing diagnostics; retain the collision envelope separately."""
import argparse,hashlib,json,math
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
root=Path('validation/yaw_integrated_candidate_v4');ip=root/'inventory.json';sp=root/'yaw_support_candidate.step';specpath=Path('docs/prototype/mechanical/sole_spacer/nut_candidate.json')
spec=json.loads(specpath.read_text());items=json.loads(ip.read_text())['parts'];solids=cq.importers.importStep(str(sp)).val().Solids();assert len(items)==len(solids)==52
parts={}
for item,solid in zip(items,solids):
 assert abs(item['volume_mm3']-solid.Volume())<1e-5
 parts[item['name']]=solid
plan={'question':'Replace the circular bearing-footprint simplification with square reference geometry without claiming thread or chamfer fidelity.',
 'source_sha256':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in [ip,sp,specpath]},
 'nut_dimensions':{'part_number':spec['part_number'],'across_flats_mm':spec['across_flats_mm'],'height_mm':spec['thickness_mm']},
 'placement':'Use each existing yaw nut centre and lower Z. The foot candidate quantity and foot Z are not reused.',
 'assumptions':['Sharp square, sides parallel to X/Y; actual face/corner chamfers unknown','Nominal 2 mm unthreaded bore remains a simplification','Lower nut face stays at existing nominal washer top'],
 'stop':'Two dimensional corner examples per eight joints; validate containment and analytic contact area. No preload, FE, adoption or parameter sweep.',
 'limits':['Minimum sharp-square case is NOT a lower bound on actual contact area; chamfers absent','No thread engagement, proof load, tool or nut rotation restraint verification','No mass or manufacturing release derived from these solids']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');rows=[]
for side in ['left','right']:
 for i in range(4):
  key=f'{side}_plate_{i}';old=parts[key+'_nut'];washer=parts[key+'_washer'];b=old.BoundingBox();x=(b.xmin+b.xmax)/2;y=(b.ymin+b.ymax)/2;z=b.zmin
  wfaces=[f for f in washer.Faces() if abs(f.BoundingBox().zmin-z)<1e-6 and abs(f.BoundingBox().zmax-z)<1e-6];assert wfaces
  for index,label in [(0,'small_sharp'),(1,'large_sharp')]:
   width=spec['across_flats_mm'][index];height=spec['thickness_mm'][index]
   shape=cq.Solid.makeBox(width,width,height,cq.Vector(x-width/2,y-width/2,z)).cut(cq.Solid.makeCylinder(1,height,cq.Vector(x,y,z)))
   assert shape.isValid() and len(shape.Solids())==1
   outside=shape.cut(old).Volume();assert outside<1e-7
   # Circumradius proves rotated outer square containment, independent of the two samples.
   assert width/math.sqrt(2)<b.xlen/2 and height<=b.zlen+1e-6
   nfaces=[f for f in shape.Faces() if abs(f.BoundingBox().zmin-z)<1e-6 and abs(f.BoundingBox().zmax-z)<1e-6]
   area=sum(f.intersect(g).Area() for f in nfaces for g in wfaces)
   analytic=width**2-math.pi*1.15**2 # actual candidate washer nominal bore radius
   assert abs(area-analytic)<1e-6
   path=a.out/f'{key}_{label}.step';cq.exporters.export(shape,str(path))
   rows.append({'joint':key,'case':label,'width_mm':width,'height_mm':height,'reference_contact_area_mm2':area,
    'outside_existing_collision_envelope_mm3':outside,'sharp_reference_step':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
(a.out/'report.json').write_text(json.dumps({'rows':rows,'actual_bearing_area_verified':False,'thread_capacity_verified':False,'formal_candidate_changed':False},indent=2)+'\n')
print(json.dumps({'cases':len(rows),'area_by_case_mm2':{label:rows[index]['reference_contact_area_mm2'] for index,label in enumerate(['small_sharp','large_sharp'])}},indent=2))
