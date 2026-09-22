"""Tab5 removal sweep against current torso and LB-020 candidates; excludes unspecified fasteners."""
import hashlib,json
from pathlib import Path
import cadquery as cq
ROOT=Path(__file__).resolve().parents[3];out=ROOT/'validation/tab5_lb020_service_v1';out.mkdir(exist_ok=True)
plan={'direction':'+X','endpoint_rear_x_mm':69,'criterion':'Swept bounding prism volume intersections <=0.01mm3 for every retained part','stop':'One straight sweep and CAD feature audit; no inference of screw sizes from generic envelope','limits':['Fasteners and cable/service loops not designed','No hand or tool envelope','Bounding prism may conservatively flag actual shape clearance']}
(out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
p=ROOT/'validation/torso_power_integration_v2';r=json.loads((p/'report.json').read_text());ss=cq.importers.importStep(str(p/'torso_candidate.step')).val().Solids();assert len(ss)==len(r['parts'])==100
parts=dict(zip([x['name'] for x in r['parts']],ss));files=[p/'report.json',p/'torso_candidate.step']
for n,f in {'tray':'validation/lb020_retention_v5/tray.step','battery':'validation/lb020_tray_v1/battery.step','strap_0':'validation/lb020_retention_v5/strap_0.step','strap_1':'validation/lb020_retention_v5/strap_1.step'}.items():
 path=ROOT/f;files.append(path);parts[n]=cq.importers.importStep(str(path)).val()
tab=parts.pop('Tab5');b=tab.BoundingBox();travel=69-b.xmin;assert travel>0
sweep=cq.Workplane('XY').box(b.xlen+travel,b.ylen,b.zlen).translate(((b.xmin+b.xmax+travel)/2,(b.ymin+b.ymax)/2,(b.zmin+b.zmax)/2)).val()
hits=[];distances=[]
for n,s in parts.items():
 v=sweep.intersect(s).Volume();distances.append({'part':n,'gap_mm':sweep.distance(s)})
 if v>.01:hits.append({'part':n,'swept_overlap_mm3':v})
from collections import Counter
cylinders=[]
for f in tab.Faces():
 if f.geomType()=='CYLINDER':
  c=f._geomAdaptor().Cylinder();loc=c.Location();axis=c.Axis().Direction()
  cylinders.append({'radius_mm':c.Radius(),'axis_location_mm':[loc.X(),loc.Y(),loc.Z()],'axis_direction':[axis.X(),axis.Y(),axis.Z()]})
result={'travel_mm':travel,'part_count':len(parts),'blocking_parts':hits,'minimum_gap':min(distances,key=lambda d:d['gap_mm']),'tab5_bbox_mm':[b.xlen,b.ylen,b.zlen],'cylindrical_faces_not_thread_specification':cylinders,'tab5_face_types':dict(Counter(f.geomType() for f in tab.Faces())),'source_sha256':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},'nominal_sweep_clear':not hits,'assembly_procedure_qualified':False,'manufacturing_release':False}
(out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
