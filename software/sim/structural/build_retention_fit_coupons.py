"""Build unpowered local fit coupons; not full-sole strength specimens."""
import argparse,json,hashlib
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
plan={'purpose':'Select fit clearance and measure print error before altering robot retention CAD','gaps_mm':[.2,.35,.5],'stem_radius_mm':2.8,'head_radius_mm':4,'head_thickness_mm':1.5,'plate_thickness_mm':3,'slide_distance_mm':8,'criteria':{'valid_single_solids':True,'sampled_overlap_max_mm3':.01},'stop_condition':'Generate three variants and check nominal insertion/slide poses once','limitations':['Local fit only; no slide lock, full foot geometry, material strength or print tolerance certification','Radial and axial gaps co-vary; measure dimensions separately before attributing fit failure','Samples do not prove continuous clearance']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
def cyl(r,z,h,x=0):return cq.Solid.makeCylinder(r,h,cq.Vector(x,0,z))
rows=[]
for g in plan['gaps_mm']:
 name=f'gap_{g:.2f}';r=2.8+g
 plate=cq.Solid.makeBox(26,16,3,cq.Vector(-9,-8,0))
 opening=cyl(r,-.01,3.02).fuse(cyl(4+g,-.01,3.02,8)).fuse(cq.Solid.makeBox(8,2*r,3.02,cq.Vector(0,-r,-.01)))
 plate=plate.cut(opening).clean()
 plug=cq.Solid.makeBox(10,10,3,cq.Vector(-5,-5,-3)).fuse(cyl(2.8,-.01,3+g+.02)).fuse(cyl(4,3+g,1.5)).clean()
 assert plate.isValid() and plug.isValid() and len(plate.Solids())==len(plug.Solids())==1
 for label,shape in [('yoke',plate),('sole',plug)]:
  cq.exporters.export(shape,str(a.out/f'{name}_{label}.step'))
  # Separate print files translated onto Z=0; assembly STEP retains common frame.
  printable=shape.translate((0,0,-shape.BoundingBox().zmin))
  cq.exporters.export(printable,str(a.out/f'{name}_{label}.stl'),tolerance=.02,angularTolerance=.05)
 poses=[(8,z) for z in [-6,-4,-2,0]]+[(x,0) for x in [6,4,2,0]]
 overlaps=[plate.intersect(plug.translate((x,0,z))).Volume() for x,z in poses]
 rows.append({'name':name,'gap_mm':g,'hole_radius_mm':r,'entry_radius_mm':4+g,'head_slot_overlap_mm':4-r,'head_bottom_z_mm':3+g,'valid_single_solids':True,'poses_dx_dz_mm':poses,'overlap_mm3':overlaps,'sampled_geometry_gate':max(overlaps)<=.01})
report={'rows':rows,'all_nominal_geometry_gates_pass':all(r['sampled_geometry_gate'] for r in rows),'manufacturing_release':False,'retention_strength_verified':False}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
(a.out/'manifest.json').write_text(json.dumps({str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(a.out.iterdir()) if f.is_file()},indent=2)+'\n')
print(json.dumps(report,indent=2))
