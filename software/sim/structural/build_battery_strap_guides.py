"""Add printed strap lateral guides; retention strength remains unqualified."""
import argparse,json,hashlib
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
source=Path('board/mechanical/prototype/rc_battery_tray_revA/tray.step');tray=cq.importers.importStep(str(source)).val()
def box(size,center):return cq.Workplane('XY').box(*size).val().translate(center)
# 10mm strap plus 0.5mm per-side nominal gap; external ribs do not cut the floor.
for y in (-6.25,6.25):
 for x in (15.3,42.7):tray=tray.fuse(box((1.5,1.5,9.5),(x,y,67.75)))
tray=tray.clean();assert tray.isValid() and len(tray.Solids())==1
paths={'battery':Path('validation/rc_battery_cad_v1_checked/battery_candidate.step'),'strap':Path('validation/battery_retention_envelope_v1/strap_envelope.step'),'yaw':Path('board/mechanical/prototype/yaw_support_candidate/revA/yaw_support_candidate.step'),'Tab5':Path('software/sim/mujoco/assets/r9_fast_turn_v1/cad/Tab5.step')}
checks=[]
for name,path in paths.items():
 s=cq.importers.importStep(str(path)).val();checks.append({'part':name,'overlap_mm3':tray.intersect(s).Volume(),'distance_mm':tray.distance(s)})
cq.exporters.export(tray,str(a.out/'tray.step'));cq.exporters.export(tray,str(a.out/'tray.stl'))
(a.out/'report.json').write_text(json.dumps({'valid_single_solid':True,'volume_mm3':tray.Volume(),'source_sha256':{str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in [source,*paths.values()]},'strap_width_mm':10,'guide_inner_gap_mm':11,'nominal_lateral_gap_each_mm':.5,'checks':checks,'release':False,'pending':['Actual strap width thickness buckle and tolerance','Guide strength and print orientation','Full insertion routing and service sequence','Pack pressure and retention loads']},indent=2)+'\n');print(checks)
