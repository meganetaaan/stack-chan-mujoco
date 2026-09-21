"""Analytical ideal-bridge DC envelope, not a physical servo current rating."""
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
catpath=Path('software/sim/actuator/catalog.json');drive=Path('software/sim/actuator/drive.py');cat=json.loads(catpath.read_text())
rows=[]
for name,m in cat['models'].items():
 cap=m['analysis_current_limit_A'];idle=m['standby_current_A']
 rows.append({'model':name,'count_per_leg':3,'count_robot':6,'motor_limit_A':cap,'standby_A':idle,'dc_draw_upper_A':cap+idle,'dc_regeneration_magnitude_upper_A':max(0,cap-idle)})
result={'scope':'Every feasible state of the existing ideal bridge under unchanged analysis current limits; not hardware or fault envelope',
 'derivation':'abs(Vterminal)<=Vbus and abs(Imotor)<=Ilimit imply -Ilimit+Iidle <= Idc=(Vterminal/Vbus)*Imotor+Iidle <= Ilimit+Iidle',
 'rows':rows,'per_leg_draw_upper_A':sum(x['count_per_leg']*x['dc_draw_upper_A'] for x in rows),'robot_draw_upper_A':sum(x['count_robot']*x['dc_draw_upper_A'] for x in rows),'robot_regeneration_upper_A':sum(x['count_robot']*x['dc_regeneration_magnitude_upper_A'] for x in rows),
 'hardware_qualified':False,'tight_bound_proven':False,'sources_sha256':{str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in (catpath,drive)},
 'exclusions':['Servo switching/conduction losses beyond fitted model','PWM pulse peak and input-capacitor inrush','Current limit implementation, faults and latency','Tab5, external logic, conversion losses and battery current'],
 'decision':'Use only as a conditional model screening envelope; do not size hardware from two turn-trace peaks or label motor-current sum as measured DC maximum'}
(a.out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
