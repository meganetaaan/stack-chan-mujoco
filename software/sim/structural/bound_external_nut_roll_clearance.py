"""Conservative continuous roll clearance bound for newly placed nut and screw."""
from pathlib import Path
import argparse,json,math,hashlib
import cadquery as cq
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
source=Path('validation/external_nut_servo_clearance_v1/report.json');r=json.loads(source.read_text())
rotating={str(i) for i in [3,9,10,11,12]}
plan={'scope':__doc__,'roll_range_rad':[-.34,.34],'criteria':{'minimum_nominal_clearance_mm':1.1},'co_rotating_targets':sorted(rotating),'bound':'d(theta)>=d(0)-2*rmax*sin(abs(theta)/2); co-rotating pairs retain d(0)','rmax':'Maximum distance to roll X axis bounded by source CAD AABB corners','stop_condition':'Evaluate bound once for two parts on each foot against all recorded neutral targets','limitations':['Existing servo motion-group assignment is an unqualified assembly hypothesis','Only nut and screw, not entire foot or harness','Tool removed during operation','No deformation, geometry tolerance or joint backlash included beyond inherited nominal margin']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');rows=[];hashes={str(source):hashlib.sha256(source.read_bytes()).hexdigest()}
for side in ['left','right']:
 for part in ['nut','screw']:
  path=Path(f'validation/sole_external_nut_v1/{side}_{part}.step');hashes[str(path)]=hashlib.sha256(path.read_bytes()).hexdigest();shape=cq.importers.importStep(str(path)).val();b=shape.BoundingBox();radius=math.hypot(max(abs(b.ymin),abs(b.ymax)),max(abs(b.zmin),abs(b.zmax)));travel=2*radius*math.sin(.34/2)
  for row in r['rows']:
   if row['side']!=side or row['part']!=part:continue
   co=row['target'] in rotating;lower=row['distance_mm']-(0 if co else travel)
   rows.append({'side':side,'part':part,'target':row['target'],'co_rotating':co,'neutral_distance_mm':row['distance_mm'],'radius_upper_mm':radius,'displacement_upper_mm':0 if co else travel,'distance_lower_mm':lower,'gate':lower>=1.1})
report={'rows':rows,'all_bounds_pass':all(x['gate'] for x in rows),'minimum_bound_mm':min(x['distance_lower_mm'] for x in rows),'source_sha256':hashes,'whole_robot_verified':False};(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='rows' and k!='source_sha256'},indent=2))
