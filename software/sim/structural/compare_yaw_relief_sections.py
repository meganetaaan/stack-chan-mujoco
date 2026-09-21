"""Compare geometric load-path sections before attempting new local FE refinement."""
import argparse,hashlib,json
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--plate-dir',type=Path,default=Path('validation/yaw_connector_plate_relief_v1'));p.add_argument('--shelf-dir',type=Path,default=Path('validation/yaw_connector_shelf_relief_v1'));a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
plan={'question':'How much material remains across the shelf/plate at and near the new connector openings?',
 'measure':'Volume of 0.1 mm X slab divided by thickness, restricted to Z86..100 mm; finite-slab average area, not exact minimum section.',
 'stations_x_mm':[-24,-19,-14,-9,-4],'stop':'One paired comparison at five fixed sections for each part and side; no mesh refinement.',
 'interpretation':'Geometry only. Do not infer strength or stiffness directly from area ratio; require relevant load resultants, boundary conditions and material allowables.'}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');rows=[];hashes={}
for side in ['left','right']:
 for kind,oldpath,newpath in [('plate',f'validation/yaw_metal_seat_v4/{side}_mount_plate.step',str(a.plate_dir/f'{side}_mount_plate.step')),('shelf',f'validation/yaw_backing_keeper_v2/{side}_yaw_fixed_support.step',str(a.shelf_dir/f'{side}_yaw_fixed_support.step'))]:
  shapes=[]
  for filename in [oldpath,newpath]:
   path=Path(filename);hashes[filename]=hashlib.sha256(path.read_bytes()).hexdigest();shapes.append(cq.importers.importStep(filename).val())
  for x in plan['stations_x_mm']:
   slab=cq.Solid.makeBox(.1,150,14,cq.Vector(x-.05,-75,86))
   areas=[shape.intersect(slab).Volume()/.1 for shape in shapes]
   assert areas[0]>0 and areas[1]<=areas[0]+1e-7
   rows.append({'side':side,'part':kind,'station_x_mm':x,'old_average_area_mm2':areas[0],'new_average_area_mm2':areas[1],'remaining_area_fraction':areas[1]/areas[0]})
(a.out/'report.json').write_text(json.dumps({'source_sha256':hashes,'rows':rows,'strength_verified':False,'manufacturing_release':False},indent=2)+'\n');print(json.dumps([x for x in rows if x['station_x_mm']==-14]))
