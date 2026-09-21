"""Analytical ideal-bridge DC envelope, not a physical servo current rating."""
import argparse,hashlib,json
import numpy as np
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
catpath=Path('software/sim/actuator/catalog.json');drive=Path('software/sim/actuator/drive.py');cat=json.loads(catpath.read_text())
jointpath=Path('board/mechanical/prototype/joints.json')
joints=json.loads(jointpath.read_text())
assigned={j['name']:next(name for name in cat['models'] if j['motor'].endswith(name)) for j in joints}
assert len(assigned)==12
rows=[]
for name,m in cat['models'].items():
 cap=m['analysis_current_limit_A'];idle=m['standby_current_A']
 counts=[sum(n.startswith(side+'_') and m==name for n,m in assigned.items()) for side in ('left','right')]
 assert counts[0]==counts[1], 'Asymmetric legs need separate envelopes'
 rows.append({'model':name,'count_per_leg':counts[0],'count_robot':sum(counts),'motor_limit_A':cap,'standby_A':idle,'dc_draw_upper_A':cap+idle,'dc_regeneration_magnitude_upper_A':max(0,cap-idle)})
result={'scope':'Every feasible state of the existing ideal bridge under unchanged analysis current limits; not hardware or fault envelope',
 'derivation':'abs(Vterminal)<=Vbus and abs(Imotor)<=Ilimit imply -Ilimit+Iidle <= Idc=(Vterminal/Vbus)*Imotor+Iidle <= Ilimit+Iidle',
 'rows':rows,'per_leg_draw_upper_A':sum(x['count_per_leg']*x['dc_draw_upper_A'] for x in rows),'robot_draw_upper_A':sum(x['count_robot']*x['dc_draw_upper_A'] for x in rows),'robot_regeneration_upper_A':sum(x['count_robot']*x['dc_regeneration_magnitude_upper_A'] for x in rows),
 'hardware_qualified':False,'tight_bound_proven':False,'sources_sha256':{str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in (catpath,drive,jointpath)},
 'exclusions':['Servo switching/conduction losses beyond fitted model','PWM pulse peak and input-capacitor inrush','Current limit implementation, faults and latency','Tab5, external logic, conversion losses and battery current'],
 'decision':'Use only as a conditional model screening envelope; do not size hardware from two turn-trace peaks or label motor-current sum as measured DC maximum'}
result['trace_crosschecks']=[]
for side in ('left','right'):
 folder=Path(f'validation/prototype_epic4_v1/load_export_{side}_v1')
 schema_path=folder/'schema.json'; data_path=folder/'loads.npz'
 names=json.loads(schema_path.read_text())['joint_names']
 assert len(names)==12 and set(names)==set(assigned)
 with np.load(data_path) as data:
  current=data['supply_current_A']
  assert current.ndim==2 and current.shape[1]==12 and np.isfinite(current).all()
  limits=np.array([cat['models'][assigned[n]]['analysis_current_limit_A'] for n in names])
  idle=np.array([cat['models'][assigned[n]]['standby_current_A'] for n in names])
  assert np.all(current<=limits+idle+1e-12), 'Per-axis draw exceeds model envelope'
  assert np.all(current>=-limits+idle-1e-12), 'Per-axis regeneration exceeds model envelope'
  draw=np.maximum(current,0).sum(axis=1); regen=np.maximum(-current,0).sum(axis=1)
  result['trace_crosschecks'].append({'turn':side,'peak_draw_A':float(draw.max()),'peak_regeneration_A':float(regen.max()),'inside_model_envelope':True,'per_axis_checked':True,'source_hashes':{str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in (schema_path,data_path)}})
(a.out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
