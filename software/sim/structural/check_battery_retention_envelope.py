import cadquery as cq,json,argparse,hashlib
from pathlib import Path
parser=argparse.ArgumentParser(description='Screen an unselected removable strap envelope, not retention strength')
parser.add_argument('--out',type=Path,required=True)
out=parser.parse_args().out;out.mkdir(parents=True,exist_ok=False)
def box(x,y,z,c):return cq.Workplane('XY').box(x,y,z).val().translate(c)
# Rectangular closed-loop envelope: removable textile strap, not a rigid printed hoop.
strap=box(28.4,10,33.5,(29,0,79.25)).cut(box(26.4,12,31.5,(29,0,79.25)))
paths={'tray':'board/mechanical/prototype/rc_battery_tray_revA/tray.step','battery':'validation/rc_battery_cad_v1_checked/battery_candidate.step','yaw_assembly':'board/mechanical/prototype/yaw_support_candidate/revA/yaw_support_candidate.step','Tab5':'software/sim/mujoco/assets/r9_fast_turn_v1/cad/Tab5.step'}
rows=[]
for name,path in paths.items():
 s=cq.importers.importStep(path).val();rows.append(dict(part=name,overlap_mm3=strap.intersect(s).Volume(),distance_mm=strap.distance(s)))
cq.exporters.export(strap,str(out/'strap_envelope.step'))
(out/'report.json').write_text(json.dumps({'sources_sha256':{name:hashlib.sha256(Path(path).read_bytes()).hexdigest() for name,path in paths.items()},'checks':rows,'width_mm':10,'thickness_mm':1,'assumptions':'Unselected textile strap envelope; buckle and overlap not included','release':False},indent=2)+'\n')
print(rows)
