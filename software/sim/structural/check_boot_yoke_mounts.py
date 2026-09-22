"""Check revised boot/yoke overlap, mounting axes and retained material near holes."""
import argparse,hashlib,json
from pathlib import Path
import cadquery as cq
from OCP.BRepAdaptor import BRepAdaptor_Surface
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[3]
if a.out.exists():p.error('new output required')
a.out.mkdir(parents=True)
paths={side:{'boot':root/f'validation/boot_rear_relief_development_v1/cad/{side}_boot_shell.step','yoke':root/f'validation/native_horn_yoke_development_v1/v4/{side}_foot_yoke.step',**{f'old_{part}':root/f'software/sim/mujoco/assets/r9_fast_turn_v1/cad/{side}_{suffix}.step' for part,suffix in [('boot','boot_shell'),('yoke','foot_yoke')]}} for side in ('left','right')}
plan={'scope':__doc__,'criteria':{'overlap_max_mm3':.01,'hole_count_per_part':4,'axis_match_tolerance_mm':1e-6,'hole_radius_mm':1.15,'protected_hole_neighborhood_radius_mm':3,'protected_z_mm':[-20,-12],'protected_removed_max_mm3':1e-6},'source_sha256':{str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for row in paths.values() for f in row.values()},'limitations':['Nominal geometry only; no screw strength, edge-distance qualification, contact preload or elastic deformation.','Retaining original material does not establish original design adequacy.']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
def holes(s):
 pts=set()
 for f in s.Faces():
  if f.geomType()!='CYLINDER':continue
  c=BRepAdaptor_Surface(f.wrapped).Cylinder()
  if abs(c.Radius()-1.15)<1e-6 and abs(c.Axis().Direction().Z())>.999999:
   q=c.Location();pts.add((round(q.X(),6),round(q.Y(),6)))
 return sorted(pts)
rows=[]
for side,row in paths.items():
 shapes={k:cq.importers.importStep(str(f)).val() for k,f in row.items()}
 b,y=shapes['boot'],shapes['yoke'];bh,yh=holes(b),holes(y)
 neighborhoods=[]
 for x,yy in bh:
  region=cq.Solid.makeCylinder(3,8,cq.Vector(x,yy,-20),cq.Vector(0,0,1))
  for part in ('boot','yoke'):
   old=shapes['old_'+part].intersect(region);new=shapes[part].intersect(region)
   neighborhoods.append({'part':part,'axis_xy_mm':[x,yy],'removed_mm3':old.cut(new).Volume(),'added_mm3':new.cut(old).Volume()})
 overlap=b.intersect(y).Volume();oldoverlap=shapes['old_boot'].intersect(shapes['old_yoke']).Volume()
 rows.append({'side':side,'boot_holes_xy_mm':bh,'yoke_holes_xy_mm':yh,'axes_match':bh==yh and len(bh)==4,'overlap_mm3':overlap,'original_overlap_mm3':oldoverlap,'distance_mm':b.distance(y),'neighborhoods':neighborhoods,'passed':bh==yh and len(bh)==4 and overlap<=.01 and all(n['removed_mm3']<=1e-6 for n in neighborhoods)})
report={'rows':rows,'all_nominal_checks_pass':all(r['passed'] for r in rows),'manufacturing_release':False}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
