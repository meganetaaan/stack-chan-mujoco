"""Nominal M3x20 fastening and tool envelopes for the reinforced yaw support.

This is assembly-access geometry, not a purchased-parts or preload release.
"""
import argparse,csv,hashlib,json
from pathlib import Path
import cadquery as cq
ROOT=Path(__file__).resolve().parents[3]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
p.add_argument('--bolt-length-mm',type=int,choices=[16,18,20],default=20)
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
config=json.loads((ROOT/'board/mechanical/engineering/yaw_fasteners.json').read_text())
base=ROOT/'software/sim/mujoco/assets/r9_fast_turn_v1/cad'
updated=ROOT/'validation/yaw_back_reinforcement_development_v1/yaw_back_reinforced_v2'
parts={}
for name in ['body_shroud','Tab5','battery_2S_reservation','battery_tray','dedicated_5V_converter','TTL_interface','left_yaw_coupler','right_yaw_coupler','left_yaw_motor_case','right_yaw_motor_case']:
 parts[name]=cq.importers.importStep(str(base/(name+'.step'))).val()
for side in ['left','right']:parts[side+'_support']=cq.importers.importStep(str(updated/(side+'_yaw_fixed_support.step'))).val()
parts['rear_cover']=cq.importers.importStep(str(ROOT/'validation/yaw_connection_development_v1/yaw_connection_v1/rear_cover_drilled.step')).val()
plan=dict(scope=__doc__,bolt_length_mm=a.bolt_length_mm,intersection_limit_mm3=.01,tool_residual_clearance_mm=.5,
          tolerance_per_surface_mm=.2,nut_driver_outer_diameter_assumed_mm=8,
          bolt_family_source='https://www.bossard.com/us-en/eshop/screws-and-bolts-with-internal-drive/hex-socket-head-cap-screws-fully-threaded/p/3/',
          status='nominal envelopes; exact purchased washer/nut/tool tolerances pending')
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
def cyl(r,length,x,y,z):return cq.Solid.makeCylinder(r,length,cq.Vector(x,y,z),cq.Vector(1,0,0))
def washer(x,y,z):return cyl(3.5,.5,x,y,z).cut(cyl(1.6,.5,x,y,z))
rows=[];checks=[]
for side in ['left','right']:
 for k,(_,dy,dz) in enumerate(config['pattern_relative_mm']):
  center=config[f'group_center_{side}_base_mm'];y,z=center[1]+dy,center[2]+dz
  envelopes={'bolt':cyl(1.5,a.bolt_length_mm,-64.5,y,z).fuse(cyl(2.75,3,-67.5,y,z)),
             'rear_washer':washer(-64.5,y,z),'inner_washer':washer(-53.5,y,z),
             'nut':cyl(3.2,2.4,-53,y,z).cut(cyl(1.25,2.4,-53,y,z)),
             'rear_key':cyl(1.5,25,-92.5,y,z),
             'nut_driver':cyl(4,25,-50.6,y,z)}
  for kind,shape in envelopes.items():
   name=f'{side}_{k}_{kind}';cq.exporters.export(shape,str(a.out/(name+'.step')))
   intersections=[];near=[]
   for part,fixed in parts.items():
    distance=float(shape.distance(fixed))
    if distance<1e-6:
     volume=float(shape.intersect(fixed).Volume())
     if volume>plan['intersection_limit_mm3']:intersections.append({'part':part,'volume_mm3':volume})
    if kind.endswith(('key','driver')) and distance<.9:
     near.append({'part':part,'distance_mm':distance,'residual_mm':distance-.4})
   checks.append({'envelope':name,'intersections':intersections,'tool_clearance_findings':near})
  rows.append(dict(side=side,id=k,y_mm=y,z_mm=z,bolt=f'M3x{a.bolt_length_mm}, class 8.8 candidate',
                   nominal_stack_mm=13.9,nominal_thread_beyond_nut_mm=a.bolt_length_mm-13.9,
                   rear_head_projection_mm=3.5,nut_shape='circumscribed cylinder; thread interface not modeled'))
with (a.out/'fasteners.csv').open('w',newline='') as f:
 writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
report=dict(scope=__doc__,rows=rows,checks=checks,
            interference_count=sum(len(r['intersections']) for r in checks),
            tool_clearance_findings=sum(len(r['tool_clearance_findings']) for r in checks),
            assembly_verified=False,
            limitations=['neutral pose subset of assembly','nominal purchased-part dimensions','nut/bolt thread overlap intentional',
                         'driver is a solid swept access envelope starting at nut front face, not a detailed socket',
                         'unmodeled leg components and cables','preload/contact not assessed'])
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ['scope','rows','checks']}))
