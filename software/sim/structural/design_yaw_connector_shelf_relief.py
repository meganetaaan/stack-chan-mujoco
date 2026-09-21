"""Coordinate shelf openings with the existing connector plate relief candidate."""
import argparse,hashlib,json,itertools
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
plan={'scope':'Candidate paired shelf/plate straight passage only; not final harness route.',
 'opening_mm':{'width':12.1,'depth':6.4,'corner_radius':1.3},'centres_xy_mm':{'left':[[-14,18],[-14,34]],'right':[[-14,-34],[-14,-18]]},
 'passage':'9.5 x 3.8 mm cross-section, Z87..97 mm; reserved corridor, not actual cable bundle.',
 'criteria':{'valid_connected_solid':True,'added_volume_max_mm3':1e-8,'radius3_seat_material_removed_max_mm3':1e-8,'nominal_passage_clearance_mm':1.3,'numeric_tolerance_mm':1e-6},
 'limits':['No printed strength/preload/creep proof','No cable bend or retention proof','No insertion/maintenance sequence proof','No adoption into revB']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');rows=[];hashes={}
for side,cy in [('left',26),('right',-26)]:
 sp=Path(f'validation/yaw_backing_keeper_v2/{side}_yaw_fixed_support.step');pp=Path(f'validation/yaw_connector_plate_relief_v1/{side}_mount_plate.step')
 for path in [sp,pp]:hashes[str(path)]=hashlib.sha256(path.read_bytes()).hexdigest()
 old=cq.importers.importStep(str(sp)).val();plate=cq.importers.importStep(str(pp)).val();new=old
 for dy in [-8,8]:
  cut=cq.Workplane('XY').box(12.1,6.4,14).edges('|Z').fillet(1.3).val().translate((-14,cy+dy,93))
  new=new.cut(cut)
 assert new.isValid() and len(new.Solids())==1
 added=new.cut(old).Volume();assert added<1e-8
 removed=old.cut(new);seats=[]
 for x,y in list(itertools.product([-27.5,2.5],[cy-8,cy+8]))+list(itertools.product([-34,8.1],[cy-10,cy+10])):
  v=removed.intersect(cq.Solid.makeCylinder(3,14,cq.Vector(x,y,86))).Volume();assert v<1e-8
  seats.append({'xy_mm':[x,y],'removed_mm3':v})
 passages=[]
 for dy in [-8,8]:
  corridor=cq.Solid.makeBox(9.5,3.8,10,cq.Vector(-18.75,cy+dy-1.9,87))
  before=old.intersect(corridor).Volume()
  ds=new.distance(corridor);dp=plate.distance(corridor)
  assert min(ds,dp)>=1.3-1e-6
  passages.append({'centre_y_mm':cy+dy,'old_shelf_overlap_mm3':before,'new_shelf_distance_mm':ds,'relieved_plate_distance_mm':dp,'allocated_residual_mm':min(ds,dp)-.8})
 cq.exporters.export(new,str(a.out/f'{side}_yaw_fixed_support.step'))
 rows.append({'side':side,'old_volume_mm3':old.Volume(),'new_volume_mm3':new.Volume(),'removed_volume_mm3':removed.Volume(),'added_volume_mm3':added,'valid_single_solid':True,'seats':seats,'passages':passages})
(a.out/'report.json').write_text(json.dumps({'source_sha256':hashes,'rows':rows,'strength_verified':False,'harness_qualified':False,'manufacturing_release':False,'current_assembly_updated':False},indent=2)+'\n');print(json.dumps([{'side':x['side'],'removed_mm3':x['removed_volume_mm3'],'passages':x['passages']} for x in rows]))
