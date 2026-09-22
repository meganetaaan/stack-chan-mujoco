"""Geometric split for purchased 0.8mm contact material; not rigid-sole release."""
import argparse,json,hashlib
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
rows=[]
for side in ['left','right']:
 src=Path(f'validation/sole_wide_seat_v1/cad/{side}_sole.step');s=cq.importers.importStep(str(src)).val();b=s.BoundingBox();h=.8
 tool=cq.Solid.makeBox(b.xlen+2,b.ylen+2,h,cq.Vector(b.xmin-1,b.ymin-1,b.zmin))
 layer=s.intersect(tool);holder=s.cut(tool)
 assert layer.isValid() and holder.isValid()
 error=abs(s.Volume()-layer.Volume()-holder.Volume());assert error<1e-5
 for name,shape in [('contact_layer',layer),('holder_envelope',holder)]:cq.exporters.export(shape,str(a.out/f'{side}_{name}.step'))
 rows.append({'side':side,'source':str(src),'sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'floor_z_mm':b.zmin,'interface_z_mm':b.zmin+h,'source_volume_mm3':s.Volume(),'contact_volume_mm3':layer.Volume(),'holder_volume_mm3':holder.Volume(),'split_volume_error_mm3':error,'holder_solids':len(holder.Solids()),'contact_solids':len(layer.Solids())})
(a.out/'report.json').write_text(json.dumps({'rows':rows,'layer_thickness_comparison_mm':.8,'material_candidate':'3M SJ5832','manufacturing_release':False,'scope':'Volume-preserving geometric segmentation; no proof of sheet cuttability, adhesion or hard-material insertion'},indent=2)+'\n');print(json.dumps(rows))
