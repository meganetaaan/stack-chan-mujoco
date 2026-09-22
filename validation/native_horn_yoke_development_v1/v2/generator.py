"""Foot-yoke candidate seated on nominal manufacturer native horn faces."""
import argparse,hashlib,json
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[3]
if a.out.exists():p.error('new output required')
a.out.mkdir(parents=True)
source=root/'validation/x330_manufacturer_cad_v1/XL_XC_330.stp';solids=cq.importers.importStep(str(source)).val().Solids()
def registered(shape):
 return shape.rotate((0,0,0),(-1,1,-1),120).translate((-3.5,0,0))
horns={'front':registered(solids[3]),'rear':registered(solids[10])}
plan=dict(scope=__doc__,front_ear_x_mm=[3,6],rear_ear_x_mm=[-29,-26],ear_thickness_mm=3,
          hole_centers_yz_mm=[[0,-6],[-6,0],[0,6],[6,0]],frame_clearance_hole_radius_mm=1.1,
          center_hole_radius_mm={'front':3.1,'rear':4},
          criteria={'valid_single_solid':True,'horn_overlap_max_mm3':.01,'minimum_mating_area_mm2':50},
          source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
          limitations=['Native CAD horn only, not HNX330-N101 metal horn','No screw length, thread strength, cap access or tolerance qualification','No full motion, structural, mass or MuJoCo release'])
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
def cyl(r,x,length,y=0,z=0):return cq.Solid.makeCylinder(r,length,cq.Vector(x,y,z),cq.Vector(1,0,0))
def faces(s,x):return [f for f in s.Faces() if f.geomType()=='PLANE' and abs(f.BoundingBox().xmin-x)<1e-5 and abs(f.BoundingBox().xmax-x)<1e-5]
rows=[]
for side in ('left','right'):
 path=root/f'software/sim/mujoco/assets/r9_fast_turn_v1/cad/{side}_foot_yoke.step'
 old=cq.importers.importStep(str(path)).val()
 # Preserve plate and its mounting holes; replace material above its top surface.
 yoke=old.cut(cq.Workplane('XY').box(200,200,100).val().translate((0,0,34)))
 for name,x in [('front',3),('rear',-29)]:
  ear=cyl(10.2,x,3).fuse(cq.Workplane('XY').box(3,18,17).val().translate((x+1.5,0,-8.5)))
  ear=ear.cut(cyl(plan['center_hole_radius_mm'][name],x-.1,3.2))
  for y,z in plan['hole_centers_yz_mm']:ear=ear.cut(cyl(1.1,x-.1,3.2,y,z))
  yoke=yoke.fuse(ear)
 yoke=yoke.clean();contacts=[]
 for name,x in [('front',3),('rear',-26)]:
  area=sum(f.intersect(g).Area() for f in faces(yoke,x) for g in faces(horns[name],x))
  overlap=yoke.intersect(horns[name]).Volume()
  contacts.append(dict(horn=name,mating_area_mm2=area,overlap_mm3=overlap,passed=area>=50 and overlap<=.01))
 valid=yoke.isValid() and len(yoke.Solids())==1
 cq.exporters.export(yoke,str(a.out/f'{side}_foot_yoke.step'))
 rows.append(dict(side=side,source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),valid_single_solid=valid,contacts=contacts,
                  volume_change_mm3=yoke.Volume()-old.Volume(),passed_nominal_geometry=valid and all(r['passed'] for r in contacts)))
(a.out/'report.json').write_text(json.dumps({'rows':rows,'manufacturing_release':False},indent=2)+'\n');print(json.dumps(rows,indent=2))
