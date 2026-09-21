"""Create a bounded connector-relief candidate without changing mounting axes."""
import argparse,hashlib,json,itertools
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--outside-port-only',action='store_true');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
margin=1.3
plan={'scope':'Metal plate only; no adoption until structure, wiring and assembly checked.',
 'relief':'9.5 x 3.8 mm housing projection offset outward by 1.3 mm, rounded corners R1.3; through plate.',
 'margin_basis':'Existing 0.5 residual plus two 0.2 tolerances and two 0.2 deflection allocations.',
 'criteria':['One valid connected solid','No added external volume','Mounting axes and existing hole material unchanged','Nominal housing distance at least 1.3 mm (numerical tolerance 1e-6)'],
 'not_verified':['Strength and fatigue','Actual manufacturing tolerance','Wire exit/bend radius','Support shelf passage','Mating geometry tolerance']}
plan['outside_port_only']=a.outside_port_only
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');rows=[];sources={}
for side,cy in [('left',26),('right',-26)]:
 path=Path(f'validation/yaw_metal_seat_v4/{side}_mount_plate.step');sources[str(path)]=hashlib.sha256(path.read_bytes()).hexdigest();old=cq.importers.importStep(str(path)).val();new=old;cuts=[];ports=[]
 for dy in ([8 if side=='left' else -8] if a.outside_port_only else [-8,8]):
  cutter=cq.Workplane('XY').box(9.5+2*margin,3.8+2*margin,5).edges('|Z').fillet(margin).val().translate((-14,cy+dy,89))
  cuts.append(cutter);new=new.cut(cutter)
  ports.append(cq.Solid.makeBox(9.5,3.8,8.1,cq.Vector(-18.75,cy+dy-1.9,78.9)))
 assert new.isValid() and len(new.Solids())==1
 added=new.cut(old).Volume();assert added<1e-8
 # Compare entire local material around all eight existing mounting axes.
 checks=[]
 for kind,axes in [('case',list(itertools.product([-27.5,2.5],[cy-8,cy+8]))),('support',list(itertools.product([-34,8.1],[cy-10,cy+10])))]:
  for x,y in axes:
   seat=cq.Solid.makeCylinder(3,5,cq.Vector(x,y,86.5))
   removed=old.cut(new).intersect(seat).Volume();assert removed<1e-8
   checks.append({'kind':kind,'axis_xy_mm':[x,y],'radius3mm_seat_removed_volume_mm3':removed})
 distances=[new.distance(port) for port in ports];assert min(distances)>=1.3-1e-6
 cq.exporters.export(new,str(a.out/f'{side}_mount_plate.step'))
 rows.append({'side':side,'old_volume_mm3':old.Volume(),'new_volume_mm3':new.Volume(),'removed_volume_mm3':old.Volume()-new.Volume(),'added_volume_mm3':added,'housing_distances_mm':distances,'seat_checks':checks,'valid_single_solid':True})
(a.out/'report.json').write_text(json.dumps({'source_sha256':sources,'rows':rows,'manufacturing_release':False,'strength_verified':False,'integrated_assembly_updated':False},indent=2)+'\n');print(json.dumps(rows))
