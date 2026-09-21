"""Nominal dual UBEC envelope layout; leads, mounts and cooling excluded."""
import argparse,json,hashlib
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--y-mm',type=float,default=25);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
def box(size,c):return cq.Workplane('XY').box(*size).val().translate(c)
paths={'yaw':Path('board/mechanical/prototype/yaw_support_candidate/revA/yaw_support_candidate.step'),'tray':Path('board/mechanical/prototype/rc_battery_tray_revB/tray.step'),'battery':Path('validation/rc_battery_cad_v1_checked/battery_candidate.step'),'Tab5':Path('software/sim/mujoco/assets/r9_fast_turn_v1/cad/Tab5.step'),'TTL':Path('software/sim/mujoco/assets/r9_fast_turn_v1/cad/TTL_interface.step')}
shapes={k:cq.importers.importStep(str(v)).val() for k,v in paths.items()}
shapes['battery_lift']=box([22,60,39],[29,0,84.5]);shapes['battery_forward']=box([73,60,30],[54.5,0,89])
modules={side:box([43.1,32.3,12.5],[-25,y,108]) for side,y in [('left',a.y_mm),('right',-a.y_mm)]}
rows=[]
for side,s in modules.items():
 cq.exporters.export(s,str(a.out/(side+'.step')))
 for name,t in shapes.items():rows.append({'module':side,'part':name,'overlap_mm3':s.intersect(t).Volume(),'distance_mm':s.distance(t)})
rows.append({'module':'left','part':'right','overlap_mm3':modules['left'].intersect(modules['right']).Volume(),'distance_mm':modules['left'].distance(modules['right'])})
(a.out/'report.json').write_text(json.dumps({'status':'nominal_envelope_screen_only','dimensions_mm':[43.1,32.3,12.5],'centers_mm':[[-25,a.y_mm,108],[-25,-a.y_mm,108]],'checks':rows,'sources_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths.values()},'excluded':['UBEC leads switches connectors mounting retention','Thermal airflow and insulation clearances','Complete new protection board and harness','Legacy converter removed in proposed replacement'],'release':False},indent=2)+'\n');print(rows)
