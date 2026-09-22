"""Conservative continuous lower insertion corridor for the no-rear-idler servo."""
import argparse,json,hashlib
from pathlib import Path
import cadquery as cq
ROOT=Path(__file__).resolve().parents[3]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
plan={'question':'Is a straight 100 mm lower insertion corridor clear before adding couplers/legs?',
 'method':'Axis-aligned bounding box of manufacturer assembly excluding pre-existing omitted rear idler indices 10/11/12, swept continuously in Z from -100 to 0 mm.',
 'stop':'One direction, both sides; if bounding corridor intersects, record inconclusive path instead of more sampling.',
 'criteria':{'intersection_mm3':.01},'criteria_source':'Inherited nominal CAD screen; tolerance/contact not qualified.',
 'limitations':['Bounding volume intersection does not prove actual servo collision','No grip/hand/cable envelope','Final shelf contact allowed by volume criterion','No case fastening proof','No installed legs/couplers']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');sources={}
def read(p):
 sources[str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest();return cq.importers.importStep(str(p)).val()
raw=read(ROOT/'validation/x330_manufacturer_cad_v1/XL_XC_330.stp').Solids()
base=ROOT/'software/sim/mujoco/assets/r9_fast_turn_v1/cad'
rear=ROOT/'validation/rear_joint_assembly_development_v1/rear_joint_inset2_v1'
parts={n:read(base/(n+'.step')) for n in ['Tab5','battery_tray','battery_2S_reservation']}
parts.update({n:read(rear/(n+'.step')) for n in ['body_shroud','rear_structural_plate']})
for side in ['left','right']:parts[side+'_support']=read(ROOT/f'validation/inset_yaw_assembly_development_v1/yaw_inset_mount_v1/{side}_yaw_fixed_support.step')
rows=[];bounds=[]
for side,y in [('left',26),('right',-26)]:
 mapped=[s.rotate((0,0,0),(1,1,0),180).translate((-5,y,68.5)) for i,s in enumerate(raw) if i not in [10,11,12]]
 b=cq.Compound.makeCompound(mapped).BoundingBox()
 corridor=cq.Solid.makeBox(b.xlen,b.ylen,b.zlen+100,cq.Vector(b.xmin,b.ymin,b.zmin-100))
 cq.exporters.export(corridor,str(a.out/f'{side}_corridor.step'))
 bounds.append({'side':side,'final_bounds':[b.xmin,b.xmax,b.ymin,b.ymax,b.zmin,b.zmax],'start_top_z_mm':b.zmax-100})
 for name,fixed in parts.items():
  v=float(corridor.intersect(fixed).Volume());d=float(corridor.distance(fixed))
  rows.append({'side':side,'target':name,'intersection_mm3':v,'distance_mm':d,'nominal_corridor_clear':v<=.01})
r={'rows':rows,'bounds':bounds,'source_sha256':sources,'manufacturing_release':False,'limitations':plan['limitations']}
(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(rows,indent=2))
