"""Conservative straight rear driver approach against the packaged yaw assembly."""
import argparse, hashlib, json, math
from pathlib import Path
import cadquery as cq
ROOT=Path(__file__).resolve().parents[3]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
plan={'question':'Does the nominal Wera driver approach fit around the current 52-part assembly?', 'stop':'Eight straight approaches, fixed 1.3 mm insertion comparison, no optimization.', 'clearance_mm':.9,'tool':{'part':'Wera 05118070001','blade_diameter_mm':4,'blade_length_mm':60,'handle_diameter_mm':13,'handle_length_mm':97},'insertion_mm':1.3,'insertion_basis':'Accu SSCF-M3-16-12-9 reference geometry; NOT adoption of grade 12.9 or proof of the current unspecified grade-8.8 socket.', 'limitations':['Socket engagement and torque not qualified','Tool dimensional tolerances unavailable; inherited .4 mm total allowance provisional','Only packaged parts; omitted corner fasteners, servo, wiring and workbench not checked','Bounding boxes conservatively enclose rotating tool and continuous straight translation']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
path=ROOT/'board/mechanical/prototype/yaw_support_candidate/revA/yaw_support_candidate.step'
solids=cq.importers.importStep(str(path)).val().Solids()
assert len(solids)==52
rows=[];excluded=[]
for side,cy in [('left',26),('right',-26)]:
 for i,(y,z) in enumerate(( (cy+dy,70+dz) for dz in [-12,12] for dy in [-7,7])):
  head=-67.7;tip=head+1.3
  # Extend behind every target: continuous entry from fully outside the assembly.
  rear=min(s.BoundingBox().xmin for s in solids)-157
  boxes={'blade':(rear,tip,y-2,y+2,z-2,z+2),'handle':(rear,tip-60,y-6.5,y+6.5,z-6.5,z+6.5)}
  excluded_here=[]
  for n,s in enumerate(solids):
   b=s.BoundingBox()
   if abs(b.xmin-head)<1e-5 and abs(b.xmax+48.7)<1e-5 and abs((b.ymin+b.ymax)/2-y)<1e-5 and abs((b.zmin+b.zmax)/2-z)<1e-5:
    excluded_here.append(n);continue
   target=(b.xmin,b.xmax,b.ymin,b.ymax,b.zmin,b.zmax)
   for kind,box in boxes.items():
    lower=math.sqrt(sum(max(0,box[k]-target[k+1],target[k]-box[k+1])**2 for k in [0,2,4]))
    rows.append({'tool':f'{side}_{i}','portion':kind,'target_solid_index':n,'aabb_distance_lower_bound_mm':lower,'clearance_proven_for_envelope':lower>=.9})
  assert len(excluded_here)==1,excluded_here
  excluded.append({'tool':f'{side}_{i}','own_bolt_solid_index':excluded_here[0],'reason':'Socket contact intentional; engagement assessed separately'})
r={'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'rows':rows,'excluded':excluded,'envelope_clearance_pass':all(x['clearance_proven_for_envelope'] for x in rows),'minimum_lower_bound_mm':min(x['aabb_distance_lower_bound_mm'] for x in rows),'assembly_qualified':False}
(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k not in ['rows','excluded']}))
