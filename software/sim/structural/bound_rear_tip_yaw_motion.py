"""Conservative continuous yaw clearance from neutral CAD distances and rotation displacement."""
import argparse,hashlib,json,math,xml.etree.ElementTree as ET
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
xml=Path('outputs/rounded_sole_fine_v1/models/scene.xml')
source=Path('validation/rear_bolt_tip_neighbors_v1/report.json')
r=json.loads(source.read_text());tree=ET.parse(xml)
for path,h in r['source_sha256'].items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==h,path
plan={'criterion':'Strictly positive continuous nominal clearance lower bound for each tip/coupler pair.',
 'method':'distance(q) >= distance(0) - 2*R*sin(max_abs_angle/2); R bounds all CAD points via bounding-box corners.',
 'stop':'16 pairs over both declared yaw joint ranges; no discretized sweep if bound proves separation.',
 'limits':['Only couplers versus protruding tips','Nominal axis and lateral placement; no tilt deflection or manufacturing error','Frozen model joint limits; not controller tracking or stop qualification']}
a.out.mkdir(parents=True,exist_ok=False);(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
rows=[];axes={}
for side in ['left','right']:
 body=tree.find(f'.//body[@name="{side}_hip_yaw"]');joint=body.find('joint')
 axis=list(map(float,joint.get('axis').split()));assert axis==[0,0,1]
 pivot=[float(x)*1000 for x in body.get('pos').split()]
 geom=body.find(f'geom[@name="vis_{side}_yaw_coupler"]')
 offset=[float(x)*1000 for x in geom.get('pos').split()]
 assert max(abs(x+y) for x,y in zip(pivot,offset))<1e-9
 assert not any(body.get(k) or geom.get(k) for k in ['quat','euler','axisangle'])
 path=Path(f'software/sim/mujoco/assets/r9_fast_turn_v1/cad/{side}_yaw_coupler.step')
 shape=cq.importers.importStep(str(path)).val();bb=shape.BoundingBox()
 radius=max(math.hypot(x-pivot[0],y-pivot[1]) for x in [bb.xmin,bb.xmax] for y in [bb.ymin,bb.ymax])
 limits=list(map(float,joint.get('range').split()));angle=max(map(abs,limits));assert angle<=math.pi
 displacement=2*radius*math.sin(angle/2)
 axes[side]={'pivot_mm':pivot,'range_rad':limits,'radius_upper_bound_mm':radius,'displacement_bound_mm':displacement}
 for c in r['checks']:
  if c['neighbor']!=f'{side}_yaw_coupler':continue
  lower=c['distance_mm']-displacement
  rows.append({'bolt':c['bolt'],'coupler':c['neighbor'],'neutral_distance_mm':c['distance_mm'],'continuous_clearance_lower_bound_mm':lower,'separation_proven':lower>0})
assert len(rows)==16
out={'sources_sha256':{str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in [xml,source]},'axes':axes,'checks':rows,
 'minimum_lower_bound_mm':min(x['continuous_clearance_lower_bound_mm'] for x in rows),'all_pairs_separated':all(x['separation_proven'] for x in rows),
 'whole_robot_dynamic_clearance_verified':False,'manufacturing_release':False,'limits':plan['limits']}
(a.out/'report.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'minimum_lower_bound_mm':out['minimum_lower_bound_mm'],'all_pairs_separated':out['all_pairs_separated']}))
