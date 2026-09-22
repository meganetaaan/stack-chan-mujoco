"""Exact box swept volumes for six straight battery-only extraction paths."""
import argparse,hashlib,json
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--tray',type=Path,default=Path('board/mechanical/prototype/rc_battery_tray_revA/tray.step'));a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
placementpath=Path('validation/rc_battery_envelope_v1/report.json');r=json.loads(placementpath.read_text());dims=r['minimum_total_extension_orientation']['oriented_size_mm'];center=r['old_center_base_mm']
base=Path('software/sim/mujoco/assets/r9_fast_turn_v1/cad')
paths={'yaw_assembly':Path('board/mechanical/prototype/yaw_support_candidate/revA/yaw_support_candidate.step'),'new_tray':a.tray}
for n in ('Tab5','dedicated_5V_converter','TTL_interface','left_yaw_motor_case','right_yaw_motor_case'):paths[n]=base/(n+'.step')
paths['body_shroud']=Path('validation/yaw_tool_access_v1/body_shroud.step')
shapes={n:cq.importers.importStep(str(path)).val() for n,path in paths.items()}
rows=[]
for axis in range(3):
 for sign in (-1,1):
  # Clear the +/-64 mm body bounds in X/Y and 0..128 in Z,
  # with a 5 mm endpoint extension (not an assembly clearance criterion).
  bound=(128 if axis==2 else 64) if sign>0 else (0 if axis==2 else -64)
  end=bound+sign*(dims[axis]/2+5);travel=abs(end-center[axis])
  size=list(dims);size[axis]+=travel;mid=list(center);mid[axis]+=sign*travel/2
  sweep=cq.Workplane('XY').box(*size).val().translate(tuple(mid))
  collisions=[]
  for name,shape in shapes.items():
   volume=sweep.intersect(shape).Volume()
   if volume>1e-6:collisions.append({'part':name,'overlap_mm3':volume})
  rows.append({'direction':'XYZ'[axis]+('+' if sign>0 else '-'),'travel_mm':travel,'swept_size_mm':size,'swept_center_mm':mid,'blocking_groups':collisions})
service=[]
# Lift 9 mm: battery bottom 74 mm clears nominal tray walls at 73 mm.
for label,size,mid in [('lift_9mm',[22,60,39],[29,0,84.5]),('forward_after_lift',[73,60,30],[54.5,0,89])]:
 sweep=cq.Workplane('XY').box(*size).val().translate(tuple(mid));hits=[]
 for name,shape in shapes.items():
  if name=='Tab5':continue
  v=sweep.intersect(shape).Volume()
  if v>1e-6:hits.append({'part':name,'overlap_mm3':v})
 service.append({'segment':label,'swept_size_mm':size,'swept_center_mm':mid,'blocking_groups':hits})
report={'method':'Union of all positions of untranslated-orientation box is exact rectangular prism; continuous path, not sampled frames','source_hashes':{str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in [placementpath,*paths.values()]},'rows':rows,'front_service_path':service,'front_service_removed_parts':['Tab5','strap'],'strap_assumed_removed':True,'cables_assumed_disconnected':True,'physical_extraction_qualified':False,'limitations':['Box omits leads, connector, swelling and handling space','No curved or rotated paths checked','Legacy converter and TTL geometry retained','Whole tray removal and housing disassembly not yet checked']}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps([(x['direction'],[y['part'] for y in x['blocking_groups']]) for x in rows]))
