"""Measure opposing horizontal bearing faces in the current foot inventory."""
import argparse,hashlib,json,math
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--out',type=Path,required=True)
a=p.parse_args()
current=Path('board/mechanical/prototype/foot_candidate/current.json')
pointer=json.loads(current.read_text());ip=Path(pointer['inventory']);inventory=json.loads(ip.read_text())
a.out.mkdir(parents=True,exist_ok=False)
plan={'scope':__doc__,'inventory':str(ip),'inventory_sha256':hashlib.sha256(ip.read_bytes()).hexdigest(),
 'revision':pointer['revision'],'criteria':{'plane_match_mm':1e-6,'reported_area_min_mm2':1e-8},
 'purpose':'Identify actual compressive load paths and nut bearing area before local structural analysis',
 'not_strength_criteria':'Positive nominal area is not joint capacity, preload, friction or contact closure',
 'stop_condition':'Each requested pair has a measured opposing-face intersection or an explicit missing bearing path'}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
rows=[]
for side in ('left','right'):
 shapes={}
 for item in inventory['parts']:
  if item['side']!=side:continue
  path=Path(item['source'])
  assert hashlib.sha256(path.read_bytes()).hexdigest()==item['sha256']
  shapes[item['part']]=cq.importers.importStep(str(path)).val()
 def faces(shape):
  out=[]
  for f in shape.Faces():
   if f.geomType()!='PLANE':continue
   n=f.normalAt()
   if abs(abs(n.z)-1)<1e-8:out.append((f.Center().z,n.z,f))
  return out
 fs={k:faces(v) for k,v in shapes.items()}
 pairs=[('boot','yoke'),('yoke','holder'),('holder','contact_layer'),
        ('holder','washer'),('washer','screw'),('yoke','nut')]
 for key in shapes:
  if key.startswith('boot_'):
   if key.endswith('_nut'):pairs.append(('boot',key))
   if key.endswith('_screw'):pairs.append(('yoke',key))
 for left,right in pairs:
  patches=[]
  for z,n,f in fs[left]:
   for zz,nn,g in fs[right]:
    if abs(z-zz)>1e-6 or n*nn>-.999999:continue
    common=f.intersect(g)
    area=common.Area()
    if area>1e-8:
     patches.append({'z_mm':z,'area_mm2':area,'centroid_mm':common.Center().toTuple(),
                     'left_outward_normal_z':n,'right_outward_normal_z':nn})
  rows.append({'side':side,'parts':[left,right],'patches':patches,
               'area_mm2':sum(x['area_mm2'] for x in patches),
               'status':'nominal_compression_path' if patches else 'no_opposing_horizontal_bearing'})
report={'rows':rows,'pair_count':len(rows),'missing_pairs':[x for x in rows if not x['patches']],
 'limitations':['No force distribution or material allowable inferred from face area',
 'No preload, separation, friction, thread strength or print variation included',
 'Vertical/curved bearing and tensile transfer are outside this horizontal-face audit',
 'Fastener shapes are envelope candidates; actual chamfers and threads may reduce bearing area'],
 'manufacturing_release':False,'strength_verified':False}
nut_path=Path('docs/prototype/mechanical/boot_fasteners/nut_candidate.json')
nut=json.loads(nut_path.read_text())
hole_r=1.15  # Nominal CAD bore; finishing tolerance not established.
ideal_areas=[af**2-math.pi*hole_r**2 for af in nut['across_flats_mm']]
old_area=4.4**2-math.pi*hole_r**2
report['boot_nut_pressure_comparison']={
 'nut_source_sha256':hashlib.sha256(nut_path.read_bytes()).hexdigest(),
 'ideal_centered_square_areas_mm2':ideal_areas,
 'old_4V4_square_cavity_floor_area_mm2':old_area,
 'mean_pressure_per_N_MPa':[1/x for x in ideal_areas],
 'mean_pressure_ratio_vs_old_full_floor':[old_area/x for x in ideal_areas],
 'assumptions':['Centered square flat nut; nominal 2.3 mm bore',
 'No chamfer, tilt, eccentricity, deformation or printing tolerance',
 'Not a guaranteed minimum contact area or local peak stress'],
 'decision':'Do not use the old uniformly loaded cavity floor as actual nut bearing; model actual contact patch and preload before strength acceptance'}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'pairs':len(rows),'missing':report['missing_pairs'],'areas':[(x['side'],x['parts'],x['area_mm2']) for x in rows]},indent=2))
