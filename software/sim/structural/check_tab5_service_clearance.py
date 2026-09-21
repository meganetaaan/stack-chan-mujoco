"""Conservative Tab5 forward-removal bounding-box clearance; fasteners not modeled."""
import argparse,hashlib,json
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
base=Path('software/sim/mujoco/assets/r9_fast_turn_v1/cad');tabpath=base/'Tab5.step';tab=cq.importers.importStep(str(tabpath)).val();b=tab.BoundingBox()
travel=64+5-b.xmin
sweep=cq.Workplane('XY').box(b.xlen+travel,b.ylen,b.zlen).val().translate(((b.xmin+b.xmax+travel)/2,(b.ymin+b.ymax)/2,(b.zmin+b.zmax)/2))
paths={'yaw_assembly':Path('board/mechanical/prototype/yaw_support_candidate/revA/yaw_support_candidate.step'),'new_tray':Path('board/mechanical/prototype/rc_battery_tray_revA/tray.step'),'battery_box':Path('validation/rc_battery_cad_v1_checked/battery_candidate.step')}
for n in ('dedicated_5V_converter','TTL_interface'):paths[n]=base/(n+'.step')
rows=[]
for name,path in paths.items():
 s=cq.importers.importStep(str(path)).val()
 rows.append({'part':name,'initial_actual_overlap_mm3':tab.intersect(s).Volume(),'swept_box_overlap_mm3':sweep.intersect(s).Volume(),'distance_to_swept_box_mm':sweep.distance(s)})
r={'direction':'base +X','travel_mm':travel,'initial_bbox_mm':[b.xmin,b.xmax,b.ymin,b.ymax,b.zmin,b.zmax],'method':'Bounding prism encloses all Tab5 poses over straight translation; overlap would require exact shape analysis, no overlap proves nominal volume clearance for included parts','rows':rows,'sources_sha256':{str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in [tabpath,*paths.values()]},'assembly_procedure_qualified':False,'pending':['Actual mounting screws and threaded depth','Tool access and removal order','Tab5 power/data cable disconnection and slack','Hand support and removal of accessories','Nominal geometry tolerances and new UBEC placement']}
(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(rows))
