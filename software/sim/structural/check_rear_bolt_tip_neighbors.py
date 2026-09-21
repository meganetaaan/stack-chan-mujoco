"""Check protruding M3 tip union against declared neutral upper-body neighbors."""
import argparse,hashlib,json
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
stack_path=Path('validation/rear_washer_stack_v1/report.json')
pack_path=Path('board/mechanical/prototype/power_packaging_revA/report.json')
stack=json.loads(stack_path.read_text());pack=json.loads(pack_path.read_text())
a.out.mkdir(parents=True,exist_ok=False)
plan={'question':'Can exposed bolt tips intersect the declared payload and yaw motor/coupler neighbors at neutral pose?',
 'criteria':{'max_overlap_mm3':.01},'criteria_origin':'Existing nominal CAD numerical overlap screening; not manufacturing clearance allowance.',
 'stop':'Eight tips against seven payload and four motor/coupler envelopes.',
 'method':'Union cylinder from earliest backing exit to furthest tip among stack cases; nominal M3 radius 1.5mm.',
 'limits':['Neutral pose only; yaw coupler rotation not swept','No lateral hole tolerance or bolt tilt','Backing plate and support mating parts excluded; this is exposed-tip clearance only','No cables or motor internal geometry','No minimum manufactured clearance certified']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
sources={str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in [stack_path,pack_path]}
def read(path,expected=None):
 path=Path(path);h=hashlib.sha256(path.read_bytes()).hexdigest()
 if expected:assert h==expected
 sources[str(path)]=h
 return cq.importers.importStep(str(path)).val()
neighbors={}
for name,(path,sha) in zip(pack['groups'],pack['sources_sha256'].items()):
 if name!='yaw_structure':neighbors[name]=read(path,sha)
base=Path('software/sim/mujoco/assets/r9_fast_turn_v1/cad')
for side in ['left','right']:
 for kind in ['yaw_motor_case','yaw_coupler']:
  neighbors[f'{side}_{kind}']=read(base/f'{side}_{kind}.step')
checks=[]
for row in stack['rows']:
 side,_,index=row['name'].split('_')
 washer=read(Path('validation/rear_washer_clearance_v1')/f'{side}_rear_{index}_rear_washer.step')
 c=washer.Center();start=min(x['exit_x_mm'] for x in row['cases']);end=max(x['tip_x_mm'] for x in row['cases'])
 tip=cq.Solid.makeCylinder(1.5,end-start,cq.Vector(start,c.y,c.z),cq.Vector(1,0,0))
 cq.exporters.export(tip,str(a.out/f'{row["name"]}_tip.step'))
 for name,shape in neighbors.items():
  d=tip.distance(shape);v=tip.intersect(shape).Volume() if d<1e-6 else 0.
  checks.append({'bolt':row['name'],'neighbor':name,'distance_mm':d,'overlap_mm3':v,'screen_pass':v<=plan['criteria']['max_overlap_mm3']})
assert len(checks)==88
report={'source_sha256':sources,'checks':checks,'failures':[x for x in checks if not x['screen_pass']],
 'nearest':min(checks,key=lambda x:x['distance_mm']),'manufacturing_release':False,'dynamic_clearance_verified':False,'limits':plan['limits']}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'failures':report['failures'],'nearest':report['nearest']}))
