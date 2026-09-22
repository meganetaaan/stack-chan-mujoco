"""Verify contact layer is a constant-thickness extrusion and export its outline."""
import argparse,hashlib,json
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
rows=[]
for side in ['left','right']:
 src=Path(f'validation/sole_contact_split_v1/{side}_contact_layer.step');s=cq.importers.importStep(str(src)).val();b=s.BoundingBox()
 faces=[f for f in s.Faces() if f.geomType()=='PLANE' and abs(f.Center().z-b.zmin)<1e-7 and abs(f.normalAt().z)>.999999]
 if len(faces)!=1:raise ValueError('Expected one planar bottom face')
 face=faces[0];rebuilt=cq.Solid.extrudeLinear(face.outerWire(),face.innerWires(),cq.Vector(0,0,b.zlen))
 missing=s.cut(rebuilt).Volume();extra=rebuilt.cut(s).Volume();ok=missing<1e-6 and extra<1e-6
 row={'side':side,'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'thickness_mm':b.zlen,'missing_mm3':missing,'extra_mm3':extra,'constant_thickness_verified':ok,'inner_cutouts':len(face.innerWires()),'area_mm2':face.Area()}
 if ok:
  flat=face.translate((0,0,-b.zmin));cq.exporters.export(cq.Workplane('XY').newObject(flat.Wires()),str(a.out/f'{side}_outline.dxf'))
 rows.append(row)
(a.out/'report.json').write_text(json.dumps({'rows':rows,'manufacturing_release':False,'scope':'Nominal sheet geometry only, no cutting allowance, material tolerance, adhesion or retention qualification'},indent=2)+'\n');print(json.dumps(rows))
