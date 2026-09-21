"""Check manufacturer STEP against DXF hole centers and fixed mounting reservations."""
import argparse, hashlib, json
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser();p.add_argument('step',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
planpath=a.out/'plan.json';plan=json.loads(planpath.read_text())
s=cq.importers.importStep(str(a.step)).val(); b=s.BoundingBox()
drillpath=Path('validation/dual_pololu_drill_v1/report.json');drill=json.loads(drillpath.read_text())
# Verify PCB surfaces, then classify components beyond these planes.
z0,z1=0.,1.5748
assert any(f.geomType()=='PLANE' and f.Area()>1000 and abs(f.Center().z-z0)<1e-6 for f in s.Faces())
assert any(f.geomType()=='PLANE' and f.Area()>1000 and abs(f.Center().z-z1)<1e-6 for f in s.Faces())
below=s.intersect(cq.Solid.makeBox(100,100,10,cq.Vector(-10,-10,-10.000001)))
above=s.intersect(cq.Solid.makeBox(100,100,20,cq.Vector(-10,-10,z1+0.000001)))
rows=[]
for x,y in drill['mount_centers_mm']:
    # Bore diameter and axis must match the STEP, not just an empty point.
    cyl=[]
    for f in s.Faces():
        fb=f.BoundingBox()
        if f.geomType()=='CYLINDER' and abs(fb.zmin-z0)<1e-6 and abs(fb.zmax-z1)<1e-6:
            if abs((fb.xmin+fb.xmax)/2-x)<0.002 and abs(fb.xlen-2.1844)<1e-6 and (abs(fb.ymin-y)<0.002 or abs(fb.ymax-y)<0.002):cyl.append(f)
    assert len(cyl)==2,(x,y,len(cyl))
    # DXF exported coordinates differ by 0.00003 mm from STEP at some holes.
    # 0.002 mm matching tolerance reflects export rounding, not physical tolerance.
    dims=plan['assumptions']; r=dims['spacer_outer_diameter_mm']/2; ri=dims['spacer_inner_diameter_mm']/2; h=dims['spacer_height_mm']
    spacer=cq.Solid.makeCylinder(r,h,cq.Vector(x,y,-h)).cut(cq.Solid.makeCylinder(ri,h,cq.Vector(x,y,-h)))
    head=cq.Solid.makeCylinder(dims['head_diameter_mm']/2,dims['head_height_mm'],cq.Vector(x,y,z1))
    row={'xy_mm':[x,y],'step_hole_diameter_mm':2.1844,'spacer_overlap_mm3':spacer.intersect(s).Volume(),'head_overlap_mm3':head.intersect(s).Volume(),'spacer_component_distance_mm':spacer.distance(below),'head_component_distance_mm':head.distance(above)}
    row['screen_pass']=max(row['spacer_overlap_mm3'],row['head_overlap_mm3'])<=plan['criteria']['maximum_overlap_mm3'] and min(row['spacer_component_distance_mm'],row['head_component_distance_mm'])>=plan['criteria']['minimum_component_clearance_mm']
    rows.append(row)
r={'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [a.step,planpath,drillpath]},'model_bounds_mm':[b.xmin,b.xmax,b.ymin,b.ymax,b.zmin,b.zmax],'pcb_z_mm':[z0,z1],'model_top_component_height_mm':b.zmax-z1,'five_volt_drawing_top_component_height_mm':6.1,'variant_discrepancy':True,'holes':rows,'all_screen_pass':all(x['screen_pass'] for x in rows),'manufacturing_release':False}
(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
