"""Generate candidate point-to-point power harness; signal electronics remain unspecified."""
import argparse,csv,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
source=Path('board/mechanical/prototype/joints.json');joints=json.loads(source.read_text());rows=[]
for j in joints:
 side=j['name'].split('_')[0]
 if side not in ('left','right'):raise ValueError(j['name'])
 for pin,net in ((1,'POWER_RETURN_STAR'),(2,side.upper()+'_SERVO_5V'),(3,side.upper()+'_DATA')):
  rows.append({'joint':j['name'],'servo_id':j['bus_id'],'connector':'J_'+j['name'],'pin':pin,'net':net,'wire_status':'unselected_for_dynamic_flex','distribution_end':'soldered_with_strain_relief_candidate'})
assert len(joints)==12 and len({j['bus_id'] for j in joints})==12
assert len(rows)==36
for side in ('left','right'):
 assert sum(r['pin']==2 and r['net']==side.upper()+'_SERVO_5V' for r in rows)==6
with (a.out/'connections.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
report={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'servo_connectors':12,'crimp_contacts':36,'power_branches':12,'positive_rails':2,'unused_second_servo_ports':12,'electrical_qualification':False,'manufacturing_release':False,'scope':'Connectivity proposal only; no cable length, conductor qualification, signal interface or protection release','constraints':['No three-wire jumper between servos; individual power returns reach distribution star','Unused second servo ports protected against accidental jumper insertion','No direct connection between left/right V+','Separate DATA segments require selected power-off-tolerant interface; do not connect directly to Tab5','Independent rail fault requests stop for both legs; rail collapse alone is not controlled stop']}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
