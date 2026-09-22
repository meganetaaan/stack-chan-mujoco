"""Audit nominal horizontal bearing interfaces of the complete candidate foot."""
import argparse,hashlib,itertools,json
from pathlib import Path
import cadquery as cq
from OCP.BRepAdaptor import BRepAdaptor_Surface
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();root=Path(__file__).resolve().parents[3];a.out.mkdir(parents=True,exist_ok=False)
paths={s:{n:root/f'validation/{folder}/{s}_{n}.step' for n,folder in [('boot_shell','boot_low_head_candidate_v1/cad'),('sole_TPU','boot_low_head_candidate_v1/cad'),('foot_yoke','native_horn_yoke_development_v1/v4')]} for s in ['left','right']}
plan={'scope':__doc__,'criteria':{'maximum_overlap_mm3':0.01,'positive_bearing_area_mm2':0},'source_sha256':{str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for q in paths.values() for f in q.values()},'limitations':['Nominal geometry only; no friction, adhesion, preload, deformation or manufacturing tolerance.','Positive area transfers compression only unless a retention mechanism is separately verified.','Ankle wrench is not automatically equal to boot/sole interface load.']};(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
def planes(shape):
 out=[]
 for f in shape.Faces():
  if f.geomType()!='PLANE':continue
  pl=BRepAdaptor_Surface(f.wrapped).Plane()
  if abs(abs(pl.Axis().Direction().Z())-1)<1e-8:out.append((pl.Location().Z(),f))
 return out
rows=[]
for side,q in paths.items():
 shapes={n:cq.importers.importStep(str(f)).val() for n,f in q.items()}
 for n,m in itertools.combinations(shapes,2):
  x,y=shapes[n],shapes[m];patches=[]
  for z,f in planes(x):
   for zz,g in planes(y):
    if abs(z-zz)>1e-6:continue
    common=f.intersect(g);area=common.Area()
    if area>1e-8:
     c=common.Center();patches.append({'z_mm':z,'area_mm2':area,'centroid_mm':[c.x,c.y,c.z]})
  overlap=x.intersect(y).Volume();rows.append({'side':side,'parts':[n,m],'distance_mm':x.distance(y),'overlap_mm3':overlap,'horizontal_patches':patches,'total_horizontal_area_mm2':sum(v['area_mm2'] for v in patches),'overlap_pass':overlap<=.01})
r={'interfaces':rows,'no_overlap':all(v['overlap_pass'] for v in rows),'load_path_strength_verified':False,'sole_retention_verified':False};(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
