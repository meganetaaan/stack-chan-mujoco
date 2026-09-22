"""Sample native foot yoke versus revised gimbal over ankle roll."""
import argparse,hashlib,json,math
from pathlib import Path
import cadquery as cq
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--gimbal-dir',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[3]
if a.out.exists():p.error('new output required')
a.out.mkdir(parents=True);angles=[i*.02 for i in range(-17,18)]
paths=[a.gimbal_dir/f'{s}_ankle_gimbal.step' for s in ('left','right')]+[root/f'validation/native_horn_yoke_development_v1/v4/{s}_foot_yoke.step' for s in ('left','right')]
plan=dict(scope=__doc__,angles_rad=angles,criteria={'overlap_max_mm3':.01,'nominal_clearance_min_mm':1.1},source_sha256={str(f.resolve().relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in paths},limitations=['Sampled pair only, not continuous sweep proof','No hardware, boot, opposite leg, floor or elastic deformation'])
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');rows=[]
for i,side in enumerate(('left','right')):
 g=cq.importers.importStep(str(paths[i])).val().translate((26,0,10));y=cq.importers.importStep(str(paths[i+2])).val()
 for angle in angles:
  moving=y.rotate((0,0,0),(1,0,0),math.degrees(angle));d=moving.distance(g);v=moving.intersect(g).Volume() if d<1e-6 else 0
  query=BRepExtrema_DistShapeShape(moving.wrapped,g.wrapped)
  if not query.IsDone(): raise RuntimeError(f'Distance query failed: {side} {angle}')
  points=[[float(c) for c in (pt.X(),pt.Y(),pt.Z())] for pt in (query.PointOnShape1(1),query.PointOnShape2(1))]
  rows.append(dict(side=side,angle_rad=angle,distance_mm=d,overlap_mm3=v,nearest_points_roll_frame_mm=points,passed=d>=1.1 and v<=.01))
r=dict(rows=rows,minimum_distance_mm=min(x['distance_mm'] for x in rows),sampled_pair_pass=all(x['passed'] for x in rows),manufacturing_release=False)
(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='rows'}))
