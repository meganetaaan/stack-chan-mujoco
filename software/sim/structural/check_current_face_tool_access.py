"""Check rotational and straight approach envelopes for a selected face-screw tool."""
import hashlib
import json
import math
from pathlib import Path
import cadquery as cq

ROOT=Path(__file__).resolve().parents[3]
SRC=ROOT/'validation/serviceable_torso_v3'
OUT=ROOT/'validation/current_face_tool_access_v1'
OUT.mkdir(exist_ok=True)
plan={
 'tool':{'manufacturer':'Wera','part':'05118068001','hex_AF_mm':2,
         'blade_length_mm':60,'blade_diameter_mm':3,'handle_length_mm':97,
         'overall_box_mm':[157,13,13],
         'source':'https://hybris-media.wera.de/download/pdfgenerator-datasheets/en/05118068001.pdf'},
 'engineering_conditions':{'socket_insertion_mm':1,'straight_approach_travel_mm':50,
         'handle_rotational_envelope_radius_mm':13*math.sqrt(2)/2,
         'screw_head_rear_x_mm':46.3,'numerical_overlap_threshold_mm3':.01},
 'method':'Union of axisymmetric blade and handle envelopes, each extended backward by approach travel; encloses all axial positions and rotations',
 'cases':['installed torso, all 115 parts','separated 10-part face unit on bench, other torso parts absent','side screws: installed torso, selected tool and 12mm screw removal'],
 'criteria':'Record all swept envelope overlaps >0.01mm3, excluding only the target screw whose socket is omitted in its CAD',
 'stop':'One selected tool; choose assembly sequence from actual blockers. Do not change shell merely to pass.',
 'limits':['Catalog dimensions are nominal, no manufacturer dimensional tolerances',
           'Tip-to-socket fit and insertion depth not proven by target-screw exclusion',
           'No hand, cable, connector, bench support or tightening torque model',
           'Bench case does not prove the transport path from the robot'],
}
(OUT/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
r=json.loads((SRC/'report.json').read_text())
ss=cq.importers.importStep(str(SRC/'assembly.step')).val().Solids()
assert len(ss)==len(r['parts'])==115
for row,s in zip(r['parts'],ss):
 assert abs(row['volume_mm3']-s.Volume())<1e-5
parts={row['name']:s for row,s in zip(r['parts'],ss)}
face={n:s for n,s in parts.items() if n=='new_carrier' or n=='Tab5' or n.endswith('_insert') or n.startswith('new_frame_screw_')}
assert len(face)==10
rows=[]
for y in [-60,60]:
 for z in [52,124]:
  target=f'new_frame_screw_{y}_{z}'
  tip=46.3+1
  # Full blade cylinder deliberately encloses the smaller hex tip.
  blade=cq.Solid.makeCylinder(1.5,60+50,cq.Vector(tip-60-50,y,z),cq.Vector(1,0,0))
  handle=cq.Solid.makeCylinder(13*math.sqrt(2)/2,97+50,cq.Vector(tip-60-97-50,y,z),cq.Vector(1,0,0))
  sweep=blade.fuse(handle)
  assert sweep.isValid()
  cq.exporters.export(sweep,str(OUT/f'tool_sweep_{y}_{z}.step'))
  for label,obstacles in [('installed',parts),('bench_face_unit',face)]:
   hits=[]; distances=[]
   for name,solid in obstacles.items():
    if name==target:continue
    v=sweep.intersect(solid).Volume()
    if v>.01:hits.append({'part':name,'overlap_mm3':v})
    distances.append((sweep.distance(solid),name))
   minimum,name=min(distances)
   rows.append({'case':label,'target':target,'overlaps':hits,
                'nominal_min_distance_mm':minimum,'nearest_part':name,
                'checked_obstacles':len(obstacles)-1})
side_rows=[]
for sign in [-1,1]:
 for z in [88,112]:
  target=f'new_{sign}_{z}_screw'
  def cyl(radius,length,start):
   return cq.Solid.makeCylinder(radius,length,cq.Vector(42,sign*start,z),cq.Vector(0,sign,0))
  # Outer head face |Y|=66; one millimetre socket insertion.
  blade=cyl(1.5,110,65)
  handle=cyl(13*math.sqrt(2)/2,147,125)
  tool=blade.fuse(handle)
  removal=cyl(1.5,22,54).fuse(cyl(2.75,14,64))
  original=cyl(1.5,10,54).fuse(cyl(2.75,2,64))
  delta=original.cut(parts[target]).Volume()+parts[target].cut(original).Volume()
  assert delta<1e-6
  for kind,envelope in [('tool',tool),('screw_removal',removal)]:
   hits=[]
   for name,solid in parts.items():
    if name==target:continue
    volume=envelope.intersect(solid).Volume()
    if volume>.01:hits.append({'part':name,'overlap_mm3':volume})
   side_rows.append({'target':target,'kind':kind,'overlaps':hits,'checked_obstacles':114,
                     'original_screw_symmetric_difference_mm3':delta})
result={'rows':rows,'side_rows':side_rows,'side_envelopes_clear':all(not x['overlaps'] for x in side_rows),'sources_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [SRC/'assembly.step',SRC/'report.json']},
        'bench_envelope_clear':all(not x['overlaps'] for x in rows if x['case']=='bench_face_unit'),
        'installed_envelope_clear':all(not x['overlaps'] for x in rows if x['case']=='installed'),
        'manufacturing_release':False,'actual_service_procedure_qualified':False}
(OUT/'report.json').write_text(json.dumps(result,indent=2)+'\n')
for row in rows:print(row['case'],row['target'],row['nominal_min_distance_mm'],[(x['part'],round(x['overlap_mm3'],3)) for x in row['overlaps']])

for row in side_rows:print(row['kind'],row['target'],row['overlaps'])
