"""Inspect nominal STEP geometry without inferring manufacturing tolerances."""
import argparse,hashlib,json
from pathlib import Path
import cadquery as cq
from OCP.BRepAdaptor import BRepAdaptor_Surface
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--step',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
s=cq.importers.importStep(str(a.step)).val();b=s.BoundingBox();rows=[]
for i,f in enumerate(s.Faces()):
 if f.geomType()=='CYLINDER':
  c=BRepAdaptor_Surface(f.wrapped).Cylinder();axis=c.Axis();v=axis.Direction();o=axis.Location()
  rows.append(dict(face=i,radius_mm=c.Radius(),axis=[v.X(),v.Y(),v.Z()],origin_mm=[o.X(),o.Y(),o.Z()],area_mm2=f.Area()))
r=dict(file_sha256=hashlib.sha256(a.step.read_bytes()).hexdigest(),solids=len(s.Solids()),valid=s.isValid(),bounds_mm={k:getattr(b,k) for k in ['xmin','xmax','ymin','ymax','zmin','zmax']},cylindrical_faces=rows)
a.out.write_text(json.dumps(r,indent=2)+'\n')
if not s.isValid():raise SystemExit('invalid STEP')
print(json.dumps({k:r[k] for k in ('solids','valid','bounds_mm')}))
