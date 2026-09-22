"""Extend boot mounting lands to the yoke plane without moving the boot."""
import argparse,hashlib,json,math
from pathlib import Path
import cadquery as cq
from OCP.BRepAdaptor import BRepAdaptor_Surface
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[3]
if a.out.exists():p.error('new output required')
a.out.mkdir(parents=True)
paths={side:{'boot':root/f'validation/boot_rear_relief_development_v1/cad/{side}_boot_shell.step','yoke':root/f'validation/native_horn_yoke_development_v1/v4/{side}_foot_yoke.step'} for side in ('left','right')}
plan={'pad_radius_mm':3,'hole_radius_mm':1.15,'pad_z_mm':[-16,-15.8],'criteria':{'single_valid_solid':True,'overlap_max_mm3':.01,'minimum_contact_area_per_pad_mm2':20},'source_sha256':{str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for row in paths.values() for f in row.values()},'limitations':['Nominal seat geometry only; print tolerances, surface flatness, preload and strength remain unverified.','Previously certified boot CAD has changed; clearance requires renewed assessment.']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
def planes(s,z):
 out=[]
 for f in s.Faces():
  if f.geomType()=='PLANE':
   pl=BRepAdaptor_Surface(f.wrapped).Plane()
   if abs(abs(pl.Axis().Direction().Z())-1)<1e-8 and abs(pl.Location().Z()-z)<1e-7:out.append(f)
 return out
rows=[]
for side,files in paths.items():
 old=cq.importers.importStep(str(files['boot'])).val();yoke=cq.importers.importStep(str(files['yoke'])).val();new=old;centers=[]
 for f in old.Faces():
  if f.geomType()=='CYLINDER':
   c=BRepAdaptor_Surface(f.wrapped).Cylinder()
   if abs(c.Radius()-1.15)<1e-6 and abs(c.Axis().Direction().Z())>.999999:
    v=c.Location();centers.append((round(v.X(),6),round(v.Y(),6)))
 centers=sorted(set(centers))
 if len(centers)!=4:raise ValueError('expected four mounting holes')
 for x,y in centers:
  pad=cq.Solid.makeCylinder(3,.21,cq.Vector(x,y,-16)).cut(cq.Solid.makeCylinder(1.15,.23,cq.Vector(x,y,-16.01)))
  new=new.fuse(pad)
 new=new.clean();areas=[]
 for x,y in centers:
  region=cq.Solid.makeCylinder(3,.4,cq.Vector(x,y,-16.1))
  area=sum(f.intersect(g).intersect(region).Area() for f in planes(new,-16) for g in planes(yoke,-16))
  areas.append({'xy_mm':[x,y],'contact_area_mm2':area})
 overlap=new.intersect(yoke).Volume();valid=new.isValid() and len(new.Solids())==1
 rows.append({'side':side,'valid_single_solid':valid,'added_volume_mm3':new.Volume()-old.Volume(),'overlap_mm3':overlap,'contact_areas':areas,'passed':valid and overlap<=.01 and all(x['contact_area_mm2']>=20 for x in areas)})
 cq.exporters.export(new,str(a.out/f'{side}_boot_shell.step'))
(a.out/'report.json').write_text(json.dumps({'rows':rows,'manufacturing_release':False},indent=2)+'\n');print(json.dumps(rows,indent=2))
