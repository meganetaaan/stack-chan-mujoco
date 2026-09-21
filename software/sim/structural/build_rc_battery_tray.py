"""New tray geometry with old sidewall attachment axes; strength not qualified."""
import argparse,json
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
def box(size,center):return cq.Workplane('XY').box(*size).val().translate(tuple(center))
blocks=[([26.4,64.4,1.5],[29,0,64.25])]
for sign in (-1,1):
 blocks += [([1.5,64.4,8],[29+sign*12.45,0,69]),([26.4,1.5,8],[29,sign*31.45,69]),([6,26,3],[29,sign*49,60.05]),([6,2,8],[29,sign*61.2,62]),([6,8,5.2],[29,sign*36,62])]
tray=box(*blocks[0])
for b in blocks[1:]:tray=tray.fuse(box(*b))
for sign in (-1,1):tray=tray.cut(cq.Solid.makeCylinder(1.1,4,cq.Vector(29,sign*59.2,63),cq.Vector(0,sign,0)))
tray=tray.clean()
assert tray.isValid() and len(tray.Solids())==1
battery=box([22,60,30],[29,0,80]);assert tray.intersect(battery).Volume()<1e-6
paths={'yaw_assembly':Path('board/mechanical/prototype/yaw_support_candidate/revA/yaw_support_candidate.step')}
base=Path('software/sim/mujoco/assets/r9_fast_turn_v1/cad')
for name in ('Tab5','dedicated_5V_converter','TTL_interface','left_yaw_motor_case','right_yaw_motor_case'):paths[name]=base/(name+'.step')
rows=[]
for name,path in paths.items():
 s=cq.importers.importStep(str(path)).val();rows.append({'part':name,'overlap_mm3':tray.intersect(s).Volume(),'distance_mm':tray.distance(s)})
cq.exporters.export(tray,str(a.out/'tray.step'));cq.exporters.export(tray,str(a.out/'tray.stl'))
r={'valid_single_solid':True,'volume_mm3':tray.Volume(),'battery_overlap_mm3':tray.intersect(battery).Volume(),'clearance_per_side_mm':.7,'clearance_status':'design assumption; not pack tolerance or swelling allowance','floor_top_mm':65,'battery_bottom_mm':65,'blocks_mm':blocks,'mount_axes_mm':[[29,-61.2,63],[29,61.2,63]],'checks':rows,'material_candidates':['PETG','ABS'],'mass_kg':None,'manufacturing_release':False,'remaining':['Retention strap and slots','Pack tolerance swelling padding and lead exit','Fasteners and preload','Load path strength and print orientation','Insertion and removal','New UBEC placement']}
(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(rows))
