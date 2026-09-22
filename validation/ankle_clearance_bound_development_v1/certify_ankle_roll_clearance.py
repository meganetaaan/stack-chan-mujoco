"""Bound local ankle CAD clearance between samples using rigid-rotation motion."""
import argparse,hashlib,json,math,sys
from pathlib import Path
import cadquery as cq

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--gimbal-dir',type=Path,required=True)
p.add_argument('--limit-rad',type=float,default=.32)
p.add_argument('--out',type=Path,required=True)
a=p.parse_args()
if a.out.exists() or not 0<a.limit_rad<=.4:p.error('new output and angle in (0,.4] required')
a.out.mkdir(parents=True)
root=Path(__file__).resolve().parents[3]
design=root/'board/mechanical/design/r5a_source';assets=root/'software/sim/mujoco/assets/r9_fast_turn_v1'
sys.path.insert(0,str(design/'cad'));import r4_geometry as geo
parts={r.name:r for r in geo.build()}
offset=json.loads((assets/'robot.json').read_text())['kinematics']['ankle_roll_offset_mm']
if list(geo.KIN['ankle_roll_offset_mm'])!=offset:raise ValueError('frame mismatch')
required=1.1
paths=[design/'cad/r4_geometry.py',design/'src/tab5_biped/core.py',design/'robot.json',assets/'robot.json',Path(__file__).resolve()]
paths.extend(a.gimbal_dir/(side+'_ankle_gimbal.step') for side in ('left','right'))
paths.extend(assets/'cad'/(side+'_'+n+'.step') for side in ('left','right') for n in ('foot_yoke','boot_shell','sole_TPU'))
plan=dict(scope=__doc__,range_rad=[-a.limit_rad,a.limit_rad],required_nominal_clearance_mm=required,
          allocation_mm={'residual':.5,'surface_tolerances_total':.4,'relative_deflection_reservation':.2},
          numerical_allowance_mm=1e-5,minimum_interval_rad=1e-4,
          bound='d(theta) >= d(midpoint) - R * half_interval; R bounds distance of every moving point to X axis via CAD bounding box',
          source_sha256={str(f.resolve().relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in paths},
          limitations=['Deflection reservation is an allocation, not FE verification.','Local CAD pairs only; no other leg, floor, harness, fasteners.','Motor shaft envelope interfaces are retained and require actual bearing design.'])
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
results=[];stationary=[]
for side in ('left','right'):
 gimbal=cq.importers.importStep(str(a.gimbal_dir/(side+'_ankle_gimbal.step'))).val()
 motor=parts[side+'_ankle_roll_motor'].shape
 dist=gimbal.distance(motor)
 original_gimbal=parts[side+'_ankle_gimbal'].shape
 original_distance=original_gimbal.distance(motor)
 stationary.append(dict(original_distance_mm=original_distance,original_overlap_mm3=original_gimbal.intersect(motor).Volume() if original_distance<1e-6 else 0,contact_interpretation='Possible mounting contact; requires explicit fastening/contact definition',side=side,pair=['gimbal','roll_motor'],distance_mm=dist,overlap_mm3=gimbal.intersect(motor).Volume() if dist<1e-6 else 0,clearance_pass=dist>=required))
 for suffix in ('foot_yoke','boot_shell','sole_TPU'):
  moving=cq.importers.importStep(str(assets/'cad'/(side+'_'+suffix+'.step'))).val();bb=moving.BoundingBox()
  radius=math.hypot(max(abs(bb.ymin),abs(bb.ymax)),max(abs(bb.zmin),abs(bb.zmax)))
  for fixed_name,fixed in [('gimbal',gimbal),('roll_motor',motor)]:
   samples={};accepted=[];unknown=[];witness=None;queue=[(-a.limit_rad,a.limit_rad)]
   def sample(angle):
    if angle not in samples:
     shape=moving.rotate((0,0,0),(1,0,0),math.degrees(angle)).translate(tuple(offset))
     samples[angle]=float(shape.distance(fixed))
    return samples[angle]
   while queue:
    lo,hi=queue.pop();mid=(lo+hi)/2
    for angle in (lo,mid,hi):
     d=sample(angle)
     if d < required+1e-5:
      witness=dict(angle_rad=angle,distance_mm=d);break
    if witness:break
    lower=sample(mid)-radius*(hi-lo)/2-1e-5
    if lower>=required:accepted.append(dict(interval_rad=[lo,hi],lower_bound_mm=lower))
    elif hi-lo<=1e-4:unknown.append([lo,hi])
    else:queue.extend([(lo,mid),(mid,hi)])
   status='sample_insufficient_guarded_margin' if witness else ('unresolved' if unknown else 'certified_local_pair')
   row=dict(side=side,moving=suffix,fixed=fixed_name,status=status,radius_bound_mm=radius,witness=witness,
            samples=[dict(angle_rad=k,distance_mm=v) for k,v in sorted(samples.items())],certified_intervals=accepted,unresolved_intervals=unknown)
   results.append(row);print(json.dumps({k:row[k] for k in ('side','moving','fixed','status','witness')}),flush=True)
report=dict(results=results,stationary=stationary,all_local_pairs_certified=all(r['status']=='certified_local_pair' for r in results) and all(r['clearance_pass'] for r in stationary),limit_expansion_approved=False)
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
