"""Geometric orientation screen, not slicer or layer strength qualification."""
import argparse,json,hashlib
from pathlib import Path
import cadquery as cq
import numpy as np
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
path=Path('board/mechanical/prototype/rc_battery_tray_revB/tray.step');s=cq.importers.importStep(str(path)).val();rows=[]
for axis in range(3):
 for sign in (-1,1):
  direction=np.zeros(3);direction[axis]=sign
  coords=[np.dot(np.array(v.Center().toTuple()),direction) for v in s.Vertices()];low=min(coords);high=max(coords);bed=0;down=0
  for f in s.Faces():
   if f.geomType()!='PLANE':continue
   normal=np.array(f.normalAt().toTuple());c=np.dot(np.array(f.Center().toTuple()),direction)
   if np.dot(normal,direction)<-0.999:
    if abs(c-low)<1e-5:bed+=f.Area()
    else:down+=f.Area()
  rows.append({'build_axis_base':'XYZ'[axis]+('+' if sign>0 else '-'),'height_mm':high-low,'lowest_planar_face_area_mm2':bed,'other_downward_planar_area_mm2':down})
(a.out/'report.json').write_text(json.dumps({'source':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'method':'Axis aligned builds; face normals opposite build direction; lowest plane area and other downward planes','limits':['No bridge span or self support analysis','No slicer supports or toolpath','No layer strength or adhesion prediction','Curved overhang surfaces excluded'],'rows':rows},indent=2)+'\n');print(rows)
