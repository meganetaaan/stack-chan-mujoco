"""Generate an internal-rib yaw support candidate within the r9 envelope.

This candidate is not released for manufacture until fastening, interference,
contact and strength verification have been completed.
"""
import argparse,hashlib,json
from pathlib import Path
import cadquery as cq

ROOT=Path(__file__).resolve().parents[3]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--wide-back',action='store_true');a=p.parse_args()
a.out.mkdir(parents=True,exist_ok=False)
rows=[]
for side,sign in [('left',1),('right',-1)]:
 source=ROOT/f'software/sim/mujoco/assets/r9_fast_turn_v1/cad/{side}_yaw_fixed_support.step'
 original=cq.importers.importStep(str(source)).val()
 shape=original
 if a.wide_back:
  shape=shape.fuse(cq.Workplane('XY').box(3,36,41.1).val().translate((-60,sign*26,70.45)))
 for y in [8,41]:
  rib=cq.Workplane('XZ').polyline([(-60,50.5),(10,88),(-60,88)]).close().extrude(3).val().translate((0,y+3,0))
  if sign<0:rib=rib.mirror('XZ')
  shape=shape.fuse(rib)
 shape=shape.clean()
 assert shape.isValid() and len(shape.Solids())==1
 b=shape.BoundingBox();ob=original.BoundingBox()
 for axis in 'xyz':
  assert getattr(b,axis+'min')>=getattr(ob,axis+'min')-1e-6
  assert getattr(b,axis+'max')<=getattr(ob,axis+'max')+1e-6
 cq.exporters.export(shape,str(a.out/(side+'_yaw_fixed_support.step')))
 rows.append({'side':side,'original_volume_mm3':original.Volume(),'candidate_volume_mm3':shape.Volume(),
              'added_PETG_mass_kg':(shape.Volume()-original.Volume())*1.27e-6,
              'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest()})
(a.out/'report.json').write_text(json.dumps({'scope':__doc__,'rows':rows,'production_verified':False,'wide_back':a.wide_back},indent=2)+'\n')
print(json.dumps(rows))
