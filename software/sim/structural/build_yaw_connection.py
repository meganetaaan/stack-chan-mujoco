"""Make a through-bolt candidate with integral lands bridging the 0.7 mm gap.

The rear cover is only a mating reference here; its load path to the body and
any backing plate remain to be designed and verified before release.
"""
import argparse,csv,hashlib,json
from pathlib import Path
import cadquery as cq

ROOT=Path(__file__).resolve().parents[3]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
a.out.mkdir(parents=True,exist_ok=False)
config=json.loads((ROOT/'board/mechanical/engineering/yaw_fasteners.json').read_text())
rows=[]
cover=cq.importers.importStep(str(ROOT/'software/sim/mujoco/assets/r9_fast_turn_v1/cad/rear_cover.step')).val()

def cylinder(r,length,x,y,z):
 return cq.Solid.makeCylinder(r,length,cq.Vector(x,y,z),cq.Vector(1,0,0))

for side in ['left','right']:
 src=ROOT/f'validation/yaw_support_development_v1/yaw_support_ribbed_v2/{side}_yaw_fixed_support.step'
 shape=cq.importers.importStep(str(src)).val()
 center=config[f'group_center_{side}_base_mm']
 for k,(_,dy,dz) in enumerate(config['pattern_relative_mm']):
  y,z=center[1]+dy,center[2]+dz
  shape=shape.fuse(cylinder(4,.7,-62.2,y,z))
  bore=cylinder(1.7,15,-70,y,z)
  shape=shape.cut(bore)
  cover=cover.cut(bore)
  shaft=cylinder(1.5,12,-64.5,y,z)
  head=cylinder(2.75,3,-67.5,y,z)
  cq.exporters.export(shaft.fuse(head),str(a.out/f'{side}_bolt_{k}_envelope.step'))
  tool=cylinder(1.5,25,-92.5,y,z)
  cq.exporters.export(tool,str(a.out/f'{side}_tool_{k}_envelope.step'))
  rows.append({'side':side,'id':k,'axis_x':1,'axis_y':0,'axis_z':0,'y_mm':y,'z_mm':z,
               'bore_mm':3.4,'bolt_thread':'M3 x 0.5','length_under_head_mm':12,
               'head_envelope_diameter_mm':5.5,'head_envelope_height_mm':3,
               'rear_washer_mm':.5,'cover_mm':1.8,'integral_land_mm':.7,'support_mm':3,
               'inner_washer_mm':.5,'nut_envelope_mm':2.4,'remaining_thread_mm':3.1,
               'qualification':'geometry candidate; exact purchased fastener tolerances, preload and backing structure pending'})
 shape=shape.clean()
 assert shape.isValid() and len(shape.Solids())==1
 cq.exporters.export(shape,str(a.out/f'{side}_yaw_fixed_support.step'))
 assert abs(shape.BoundingBox().xmin+62.2)<1e-6
cq.exporters.export(cover,str(a.out/'rear_cover_drilled.step'))
with (a.out/'fasteners.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
report={'scope':__doc__,'fasteners':rows,'integral_land_depth_mm':.7,
        'additional_rear_head_protrusion_beyond_original_cover_mm':3.5,
        'remaining':['cover/backing structure strength','bolt-to-hole contact','preload retention','physical fastener tolerances','assembly access across full robot','external yaw bearing support'],
        'production_verified':False}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'supports':2,'bolt_envelopes':8,'rear_projection_mm':3.5,'production_verified':False}))
