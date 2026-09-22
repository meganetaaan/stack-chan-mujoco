"""Map star-harness branches to motor-case bodies and crossed joints."""
import argparse,csv,hashlib,json
from pathlib import Path
import xml.etree.ElementTree as ET
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
model=Path('software/sim/mujoco/assets/r9_fast_turn_v1/models/scene.xml')
harness=Path('schematics/power/split_servo_harness_revA/connections.csv')
root=ET.parse(model).getroot();parents={c:p for p in root.iter() for c in p}
connections=list(csv.DictReader(harness.open()));branches=[];crossings={}
for joint in dict.fromkeys(x['joint'] for x in connections):
 side=joint.split('_')[0]
 geom_name=f'vis_{side}_yaw_motor_case' if joint.endswith('hip_yaw') else f'vis_{joint}_motor'
 geoms=root.findall(f'.//geom[@name="{geom_name}"]');assert len(geoms)==1,geom_name
 body=parents[geoms[0]];assert body.tag=='body'
 owner=body.attrib['name'];chain=[]
 while body.attrib.get('name')!='base':
  assert body.tag=='body'
  chain.extend(j.attrib['name'] for j in body.findall('joint'))
  body=parents[body]
 chain.reverse()
 for name in chain:crossings.setdefault(name,[]).append(joint)
 branch_rows=[x for x in connections if x['joint']==joint]
 assert {x['pin'] for x in branch_rows}=={'1','2','3'}
 branches.append({'servo':joint,'motor_case_geom':geom_name,'case_owner_body':owner,
  'crossed_joints_from_base':chain,'conductor_count':3,'connector_local_position_m':None})
report={'source_sha256':{str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in [model,harness]},
 'branches':branches,'joint_crossings':{k:{'branches':v,'conductors':3*len(v)} for k,v in crossings.items()},
 'assumptions':['Distribution and host interface are on base.',
 'Routes follow the model body ancestry without an alternative external bypass.'],
 'limits':['Motor mesh ownership follows the current model; verify against real connector and mounting drawings.',
 'Joint label is not automatically the body carrying its motor connector.',
 'No connector positions, geometric route, bend radius, length, clearance, fatigue or mass qualification.',
 'Crossing counts include DATA per existing star-harness proposal; changing topology requires electrical review.'],
 'manufacturing_release':False}
a.out.mkdir(parents=True,exist_ok=False);(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report['joint_crossings']))
