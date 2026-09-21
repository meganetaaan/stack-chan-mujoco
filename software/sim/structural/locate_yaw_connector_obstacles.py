"""Identify structural neighbours of actual yaw connector housings."""
import argparse,hashlib,json
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--step',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
refpath=Path('validation/servo_reference_geometry_v1/report.json');ref=json.loads(refpath.read_text());assert hashlib.sha256(a.step.read_bytes()).hexdigest()==ref['source_sha256']
ptrpath=Path('board/mechanical/prototype/yaw_support_candidate/current.json');ptr=json.loads(ptrpath.read_text());invpath=Path(ptr['inventory']);inv=json.loads(invpath.read_text())
parts=[x for x in inv['parts'] if x['name'] in ['body_shroud','rear_plate'] or x['name'].endswith(('yaw_fixed_support','threaded_backing_plate','mount_plate'))]
sources={str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in [refpath,ptrpath,invpath]};shapes={}
for x in parts:
 path=Path(x['source']);h=hashlib.sha256(path.read_bytes()).hexdigest();assert h==x['source_sha256'];sources[str(path)]=h;shapes[x['name']]=cq.importers.importStep(str(path)).val()
raw=cq.importers.importStep(str(a.step)).val().Solids();rows=[]
for side,y in [('left',26),('right',-26)]:
 for idx in [13,14]:
  port=raw[idx].rotate((0,0,0),(1,1,0),180).translate((-5,y,68.5))
  b=port.BoundingBox()
  neighbours=sorted([{'part':name,'distance_mm':float(port.distance(shape))} for name,shape in shapes.items()],key=lambda x:x['distance_mm'])
  # Proposed 10 mm straight service corridor beyond the nominal outer face.
  # Bounding-box cross-section deliberately over-approximates the port.
  direction=[0,0,1]
  corridor=cq.Solid.makeBox(b.xlen,b.ylen,10,cq.Vector(b.xmin,b.ymin,b.zmax))
  corridor_checks=[{'part':name,'overlap_mm3':float(corridor.intersect(shape).Volume()),'distance_mm':float(corridor.distance(shape))} for name,shape in shapes.items()]
  rows.append({'side':side,'manufacturer_solid_index':idx,'bounds_min_mm':[b.xmin,b.ymin,b.zmin],'bounds_max_mm':[b.xmax,b.ymax,b.zmax],'structural_neighbours':neighbours,'corridor_direction_xyz':direction,'corridor_length_mm':10,'corridor_checks':corridor_checks})
r={'source_sha256':sources,'rows':rows,'scope':'Nominal connector housing to eight structural parts only; fasteners and mating cable excluded.','corridor_status':'Corrected +Z approach direction: native +Z contains three board-tail pins, so native -Z is mating side. 10 mm remains a proposed service reservation, not manufacturer insertion dimension; structural parts only', 'placement':'Same hypothesis as yaw_current_manufacturer_fit_v2','manufacturing_release':False}
a.out.mkdir(parents=True,exist_ok=False);(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps([{'side':x['side'],'port':x['manufacturer_solid_index'],'nearest':x['structural_neighbours'][:2]} for x in rows]))
