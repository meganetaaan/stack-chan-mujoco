"""Local roof openings for existing yaw case driver corridors; no screw retention claim."""
import argparse,json,hashlib
from pathlib import Path
import cadquery as cq
ROOT=Path(__file__).resolve().parents[3]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
plan={'question':'Can local roof holes remove the eight known yaw driver collisions while preserving outer bounds?',
 'stop':'One 6 mm opening candidate at the eight matched axes; no FE or size sweep.',
 'design_basis':'4 mm provisional driver + 2*(0.4 mm existing tolerance budget + 0.5 mm residual) = 5.8 mm minimum nominal diameter; choose 6 mm nominal for 0.1 mm additional radial margin.',
 'criteria':{'tool_nominal_clearance_mm':.9,'maximum_intersection_mm3':.01,'unchanged_outer_bounds_mm':.000001},
 'limitations':['Driver size is still provisional','Roof strength and local stress redistribution unverified','Case screw engagement unresolved','No hand/handle sweep or purchased tool proof']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
source=ROOT/'validation/rear_joint_assembly_development_v1/rear_joint_inset2_v1/body_shroud.step'
body=cq.importers.importStep(str(source)).val();old=body.Volume();bb=body.BoundingBox()
axes=[(side,x,y) for side,cy in [('left',26),('right',-26)] for x in [-27.5,2.5] for y in [cy-8,cy+8]]
for side,x,y in axes:body=body.cut(cq.Solid.makeCylinder(3,50,cq.Vector(x,y,91)))
body=body.clean();assert body.isValid() and len(body.Solids())==1
b=body.BoundingBox();delta=max(abs(getattr(b,k)-getattr(bb,k)) for k in ['xmin','xmax','ymin','ymax','zmin','zmax']);assert delta<=1e-6
rows=[]
for side,x,y in axes:
 tool=cq.Solid.makeCylinder(2,50,cq.Vector(x,y,91));d=float(tool.distance(body));v=float(tool.intersect(body).Volume()) if d<1e-6 else 0
 rows.append({'side':side,'x_mm':x,'y_mm':y,'distance_mm':d,'residual_after_0_4_mm_budget':d-.4,'intersection_mm3':v,'pass':d>=.9 and v<=.01})
cq.exporters.export(body,str(a.out/'body_shroud.step'))
r={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'rows':rows,'all_target_tool_checks_pass':all(x['pass'] for x in rows),'removed_volume_mm3':old-body.Volume(),'outer_bounds_max_change_mm':delta,'valid_solids':1,'manufacturing_release':False,'strength_verified':False,'limitations':plan['limitations']}
(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
