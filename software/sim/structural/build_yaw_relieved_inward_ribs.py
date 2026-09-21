"""Inward rib candidate with screw-column relief in added material only, preserving the existing bounding envelope."""
import argparse,hashlib,json
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
plan={'question':'Can inward-thickened existing side ribs stiffen the front shelf without enlarging the envelope or blocking fixed hardware?',
 'candidate':'Two cheeks X-30..10, local Y[-18,-11.5] and [11.5,18], Z70..88; overlap existing side ribs, stop below plate pocket.',
 'screw_relief': 'Radius 2.7 mm vertical columns through added material only; existing support untouched. Tool access not qualified.',
 'assumptions':{'rib_thickness_mm':6.5,'lower_z_mm':70,'material':'printed ABS/PETG, grade and printing not qualified'},
 'criteria':['valid single solid','unchanged bounding box','added-material overlap with fixed assembly and manufacturer case/connectors <=0.01 mm3','reserved outer-port corridor distance >=1.3 mm'],
 'stop':'One geometry, both sides; no parameter sweep or release.',
 'limits':['No stiffness/strength evaluation yet','No full moving-assembly clearance','No physical tool or printing qualification','Rear idler is not in current build and is not introduced here']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
inv=Path('board/mechanical/prototype/yaw_support_candidate/revB/inventory.json');parts=json.loads(inv.read_text())['parts']
servo_path=Path('validation/x330_manufacturer_cad_v1/XL_XC_330.stp');solids=cq.importers.importStep(str(servo_path)).val().Solids()
hashes={str(inv):hashlib.sha256(inv.read_bytes()).hexdigest(),str(servo_path):hashlib.sha256(servo_path.read_bytes()).hexdigest()};rows=[]
assembly_path=Path('board/mechanical/prototype/yaw_support_candidate/revB/yaw_support_candidate.step')
fixed=cq.importers.importStep(str(assembly_path)).val();hashes[str(assembly_path)]=hashlib.sha256(assembly_path.read_bytes()).hexdigest()
for side,cy in [('left',26),('right',-26)]:
 path=Path(f'validation/yaw_rail_seat_v1/{side}_yaw_fixed_support.step');hashes[str(path)]=hashlib.sha256(path.read_bytes()).hexdigest()
 old=cq.importers.importStep(str(path)).val();webs=[cq.Solid.makeBox(40,6.5,18,cq.Vector(-30,cy+dy,70)) for dy in [-18,11.5]];raw=old.fuse(*webs).clean();added=raw.cut(old)
 reliefs=[]
 members=fixed.Solids();assert len(members)==len(parts)
 for item,solid in zip(parts,members):
  assert abs(solid.Volume()-item['volume_mm3'])<.001
  if item['name'] in [side+'_plate_2_screw',side+'_plate_3_screw']:
   b=solid.BoundingBox();x=(b.xmin+b.xmax)/2;y=(b.ymin+b.ymax)/2
   reliefs.append(cq.Solid.makeCylinder(2.7,30,cq.Vector(x,y,65)))
 assert len(reliefs)==2
 added=added.cut(*reliefs).clean();new=old.fuse(added).clean()
 assert old.cut(new).Volume()<1e-6
 before=old.BoundingBox();after=new.BoundingBox();delta=max(abs(getattr(before,k)-getattr(after,k)) for k in ['xmin','xmax','ymin','ymax','zmin','zmax'])
 collisions=[]
 overlap=added.intersect(fixed).Volume()
 if overlap>.01:
  members=fixed.Solids();assert len(members)==len(parts)
  for item,solid in zip(parts,members):
   assert abs(solid.Volume()-item['volume_mm3'])<.001
   volume=added.intersect(solid).Volume()
   if volume>.01:collisions.append({'part':item['name'],'added_overlap_mm3':volume})
 placed=cq.Compound.makeCompound([solids[i].rotate((0,0,0),(1,1,0),180).translate((-5,cy,68.5)) for i in [0,1,2,13,14]])
 servo_overlap=added.intersect(placed).Volume();servo_gap=added.distance(placed)
 dy=8 if side=='left' else -8;corridor=cq.Solid.makeBox(9.5,3.8,10,cq.Vector(-18.75,cy+dy-1.9,87));gap=new.distance(corridor)
 passed=new.isValid() and len(new.Solids())==1 and delta<1e-6 and not collisions and servo_overlap<=.01 and gap>=1.3-1e-6
 cq.exporters.export(new,str(a.out/f'{side}_yaw_fixed_support.step'))
 rows.append({'side':side,'valid_single_solid':new.isValid() and len(new.Solids())==1,'bbox_change_mm':delta,'added_volume_mm3':added.Volume(),'fixed_collisions':collisions,'manufacturer_overlap_mm3':servo_overlap,'manufacturer_gap_to_addition_mm':servo_gap,'corridor_gap_mm':gap,'geometry_screen_pass':passed})
(a.out/'report.json').write_text(json.dumps({'source_sha256':hashes,'rows':rows,'manufacturing_release':False},indent=2)+'\n');print(json.dumps(rows,indent=2))
