"""Local CAD sweep of ankle roll; every moving/fixed pair retained."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
import cadquery as cq
from OCP.BRepExtrema import BRepExtrema_DistShapeShape

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--gimbal-dir',type=Path,help='Optional alternative ankle gimbal STEP directory')
p.add_argument('--out',type=Path,required=True)
a=p.parse_args()
root=Path(__file__).resolve().parents[3]
if a.out.exists():p.error('new output required')
a.out.mkdir(parents=True)
design=root/'board/mechanical/design/r5a_source'
sys.path.insert(0,str(design/'cad'))
import r4_geometry as geo
parts={r.name:r for r in geo.build()}
assets=root/'software/sim/mujoco/assets/r9_fast_turn_v1'
robot=json.loads((assets/'robot.json').read_text())
offset=robot['kinematics']['ankle_roll_offset_mm']
if list(geo.KIN['ankle_roll_offset_mm']) != offset:
 raise RuntimeError('Ankle frame mismatch')
angles=[-.34,-.32,-.30,-.28,-.24,0,.24,.28,.30,.32,.34]
paths=[design/'cad/r4_geometry.py',design/'src/tab5_biped/core.py',design/'robot.json',assets/'robot.json']
plan=dict(scope=__doc__,angles_rad=angles,roll_axis=[1,0,0],roll_origin_in_pitch_mm=offset,
          criteria={'overlap_max_mm3':.01,'nominal_noncontact_clearance_mm':.9},
          limitations=['Local pitch-body versus roll-body geometry only; shin, opposite foot, floor, cables and fasteners absent.',
                       '0.9 mm clearance screen is 0.5 mm residual plus two 0.2 mm surface tolerances; no deflection/sweep margin.',
                       'Motor envelope includes conservative shaft keepouts; bearing/mating interfaces require separate interpretation.',
                       'Discrete sampled angles do not establish swept-volume safety or authorize wider software limits.'])
paths.extend(assets/'cad'/(side+'_'+n+'.step') for side in ('left','right') for n in ('foot_yoke','boot_shell','sole_TPU'))
if a.gimbal_dir:
 paths.extend(a.gimbal_dir/(side+'_ankle_gimbal.step') for side in ('left','right'))
 plan['alternative_gimbal_directory']=str(a.gimbal_dir)
plan['source_sha256']={str(f.resolve().relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in paths}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
rows=[]
for side in ('left','right'):
 fixed={side+'_'+n:parts[side+'_'+n].shape for n in ('ankle_gimbal','ankle_roll_motor')}
 if a.gimbal_dir:
  fixed[side+'_ankle_gimbal']=cq.importers.importStep(str(a.gimbal_dir/(side+'_ankle_gimbal.step'))).val()
 moving={side+'_'+n:cq.importers.importStep(str(assets/'cad'/(side+'_'+n+'.step'))).val() for n in ('foot_yoke','boot_shell','sole_TPU')}
 for angle in angles:
  for name,shape in moving.items():
   transformed=shape.rotate((0,0,0),(1,0,0),math.degrees(angle)).translate(tuple(offset))
   for fixed_name,fixed_shape in fixed.items():
    query=BRepExtrema_DistShapeShape(transformed.wrapped,fixed_shape.wrapped)
    if not query.IsDone():raise RuntimeError("CAD distance query failed")
    distance=float(query.Value())
    points=[[float(v) for v in (point.X(),point.Y(),point.Z())] for point in (query.PointOnShape1(1),query.PointOnShape2(1))]
    volume=float(transformed.intersect(fixed_shape).Volume()) if distance<1e-6 else 0
    rows.append(dict(side=side,angle_rad=angle,moving=name,fixed=fixed_name,distance_mm=distance,nearest_points_pitch_frame_mm=points,overlap_mm3=volume,
                     overlap_pass=volume<=.01,nominal_clearance_pass=distance>=.9))
report=dict(rows=rows,overlap_findings=[r for r in rows if not r['overlap_pass']],minimum_distance_mm=min(r['distance_mm'] for r in rows),
            all_nominal_clearance_pass=all(r['nominal_clearance_pass'] for r in rows),limit_expansion_approved=False)
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='rows'},indent=2))
