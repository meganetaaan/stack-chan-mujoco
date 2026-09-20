"""Sample revised boot against manufacturer X330 assembly with explicit motion groups."""
import argparse,hashlib,json,math
from pathlib import Path
import cadquery as cq
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[3]
if a.out.exists():p.error('new output required')
a.out.mkdir(parents=True)
step=root/'validation/x330_manufacturer_cad_v1/XL_XC_330.stp'
mapping=root/'validation/x330_component_map_v1/report.json';meta=json.loads(mapping.read_text())
if hashlib.sha256(step.read_bytes()).hexdigest()!=meta['source_sha256']:raise ValueError('mapping source mismatch')
parts=cq.importers.importStep(str(step)).val().Solids()
if len(parts)!=len(meta['components']):raise ValueError('component count mismatch')
parts=[s.rotate((0,0,0),(-1,1,-1),120).translate((-3.5,0,0)) for s in parts]
boot_dir=root/'validation/boot_rear_relief_development_v1/cad'
angles=[-.34,-.32,-.30,-.28,-.24,0,.24,.28,.30,.32,.34]
rotating={3,9,10,11,12}
paths=[step,mapping,Path(__file__).resolve(),*[boot_dir/f'{s}_boot_shell.step' for s in ('left','right')]]
plan={'scope':__doc__,'angles_rad':angles,'assumed_rotating_component_indices':sorted(rotating),'nominal_clearance_min_mm':1.1,'overlap_max_mm3':.01,'source_sha256':{str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in paths},'limitations':['Discrete samples, not continuous clearance proof.','Horn, idler, cap and center screws co-rotate as an explicit hypothesis; cap/screw assembly motion needs qualification.','Manufacturer CAD has no dimensional tolerance guarantee.','No new mounting screws, harness or elastic deformation included.']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');rows=[]
for side in ('left','right'):
 boot=cq.importers.importStep(str(boot_dir/f'{side}_boot_shell.step')).val()
 for angle in angles:
  b=boot.rotate((0,0,0),(1,0,0),math.degrees(angle))
  for i,part in enumerate(parts):
   fixed=part.rotate((0,0,0),(1,0,0),math.degrees(angle)) if i in rotating else part
   q=BRepExtrema_DistShapeShape(b.wrapped,fixed.wrapped)
   if not q.IsDone():raise RuntimeError('distance query failed')
   d=float(q.Value());v=b.intersect(fixed).Volume() if d<1e-6 else 0
   pts=[[p.X(),p.Y(),p.Z()] for p in [q.PointOnShape1(1),q.PointOnShape2(1)]]
   rows.append({'side':side,'angle_rad':angle,'component_index':i,'product_name':meta['components'][i]['product_name'],'distance_mm':d,'overlap_mm3':v,'nearest_points_roll_frame_mm':pts,'passed':d>=1.1 and v<=.01})
 result=[r for r in rows if r['side']==side]
 print(json.dumps({'side':side,'minimum_distance_mm':min(r['distance_mm'] for r in result),'failed_samples':sum(not r['passed'] for r in result)}),flush=True)
(a.out/'report.json').write_text(json.dumps({'rows':rows,'all_sampled_pairs_pass':all(r['passed'] for r in rows),'manufacturing_release':False},indent=2)+'\n')
