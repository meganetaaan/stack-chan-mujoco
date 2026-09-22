"""Relieve rear gimbal bridge and upper corners while retaining ankle axes."""
import argparse,hashlib,json,sys
from pathlib import Path
import cadquery as cq

p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[3]
if a.out.exists():p.error('new output required')
a.out.mkdir(parents=True)
source=root/'board/mechanical/design/r5a_source/cad/r4_geometry.py'
sys.path.insert(0,str(source.parent));import r4_geometry as geo
plan=dict(scope=__doc__,rear_bridge_forward_shift_mm=.8,upper_rear_corner_z_max_mm=17.5,lower_bridge_upward_shift_mm=1.2,
          criteria={'valid_single_solid':True,'no_outer_envelope_growth':True},
          source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
          limitations=['Local CAD candidate, no structural or fastening qualification','Nominal geometry only; no cable/fastener clearances','No joint limit changes authorized'])
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
parts={p.name:p for p in geo.build()};rows=[]
for side,sign in [('left',1),('right',-1)]:
 old=parts[side+'_ankle_gimbal'].shape
 # Translate the lower crossbar forward without reducing its 2.4 mm thickness.
 cutter=cq.Workplane('XY').box(20,60,4.8002).val().translate((-55,sign*1.95,-21.2))
 extension=cq.Workplane('XY').box(2.4,34.9,2.4).val().translate((-54.2,sign*1.95,-17.6))
 new=old.cut(cutter).fuse(extension)
 top_cut=cq.Workplane('XY').box(30,60,10).val().translate((-45,0,22.5))
 new=new.cut(top_cut).clean()
 b0,b1=old.BoundingBox(),new.BoundingBox()
 no_growth=all(getattr(b1,axis+'min')>=getattr(b0,axis+'min')-1e-6 and getattr(b1,axis+'max')<=getattr(b0,axis+'max')+1e-6 for axis in 'xyz')
 rows.append(dict(side=side,old_volume_mm3=old.Volume(),new_volume_mm3=new.Volume(),gates={'valid_single_solid':new.isValid() and len(new.Solids())==1,'no_outer_envelope_growth':no_growth}))
 cq.exporters.export(new,str(a.out/(side+'_ankle_gimbal.step')))
(a.out/'report.json').write_text(json.dumps({'rows':rows,'structural_verified':False},indent=2)+'\n');print(json.dumps(rows))
