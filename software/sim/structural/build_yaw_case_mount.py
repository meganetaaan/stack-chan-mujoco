"""Match rear case bore axes and drill nominal shelf clearance holes."""
import argparse,json,hashlib
from pathlib import Path
import cadquery as cq
ROOT=Path(__file__).resolve().parents[3]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
plan={'question':'Do drawing-derived rear case axes match STEP, and can a shelf clearance-hole candidate use them?',
 'stop':'One 2.3 mm hole candidate on both supports; no FE or dimension sweep.',
 'assumptions':{'clearance_hole_diameter_mm':2.3,'tool_radius_mm':2,'tool_length_mm':50},
 'criteria':{'axis_match_mm':.001,'tool_nominal_clearance_mm':.9,'intersection_mm3':.01},
 'limitations':['Tool is a reservation, not purchased screwdriver','No screw head seating, thread depth or preload proof','Reference manufacturer drawing and nominal STEP','Do not manufacture until screw insertion limits are resolved']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');sources={}
def read(p):
 sources[str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest();return cq.importers.importStep(str(p)).val()
raw=read(ROOT/'validation/x330_manufacturer_cad_v1/XL_XC_330.stp').Solids()
base=ROOT/'software/sim/mujoco/assets/r9_fast_turn_v1/cad'
targets={n:read(base/(n+'.step')) for n in ['Tab5','battery_tray','battery_2S_reservation','dedicated_5V_converter','TTL_interface']}
rear=ROOT/'validation/rear_joint_assembly_development_v1/rear_joint_inset2_v1'
targets['body_shroud']=read(rear/'body_shroud.step')
rows=[];tools=[]
for side,cy in [('left',26),('right',-26)]:
 case=raw[2].rotate((0,0,0),(1,1,0),180).translate((-5,cy,68.5))
 cylinders=[]
 for f in case.Faces():
  if f.geomType()!='CYLINDER':continue
  c=f._geomAdaptor().Cylinder();v=c.Axis().Direction();o=c.Location();b=f.BoundingBox()
  if abs(v.Z())>.999:cylinders.append({'x':o.X(),'y':o.Y(),'radius':c.Radius(),'zmin':b.zmin,'zmax':b.zmax})
 support=read(ROOT/f'validation/inset_yaw_assembly_development_v1/yaw_inset_mount_v1/{side}_yaw_fixed_support.step');before=support.Volume()
 for x in [-27.5,2.5]:
  for y in [cy-8,cy+8]:
   matches=[c for c in cylinders if abs(c['x']-x)<.001 and abs(c['y']-y)<.001 and abs(c['radius']-1.0)<.001]
   assert matches,('unmatched rear clearance bore',side,x,y)
   # Cut only the shelf at Z=88..91; do not alter case or underlying ribs.
   hole=cq.Solid.makeCylinder(1.15,3.02,cq.Vector(x,y,87.99))
   support=support.cut(hole)
   rows.append({'side':side,'x_mm':x,'y_mm':y,'rear_face_z_mm':88,'matched_rear_clearance_faces':matches})
   tool=cq.Solid.makeCylinder(2,50,cq.Vector(x,y,91))
   for n,t in targets.items():
    d=float(tool.distance(t));v=float(tool.intersect(t).Volume()) if d<1e-6 else 0
    tools.append({'side':side,'x_mm':x,'y_mm':y,'target':n,'distance_mm':d,'overlap_mm3':v,'pass':d>=.9 and v<=.01})
 support=support.clean();assert support.isValid() and len(support.Solids())==1
 cq.exporters.export(support,str(a.out/f'{side}_yaw_fixed_support.step'))
 rows.append({'side':side,'removed_volume_mm3':before-support.Volume(),'solid_valid':True})
r={'holes_and_shapes':rows,'tool_checks':tools,'tool_clearance_pass':all(t['pass'] for t in tools),'source_sha256':sources,'manufacturing_release':False,'strength_verified':False,'limitations':plan['limitations']}
(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'matched_axes':8,'tool_failures':[t for t in tools if not t['pass']]},indent=2))
