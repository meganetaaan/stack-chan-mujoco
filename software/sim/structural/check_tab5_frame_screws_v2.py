"""Nominal M3x8 face screws: dimensional reservation, engagement unqualified."""
import hashlib,json
from pathlib import Path
import cadquery as cq
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'validation/tab5_frame_screws_v2';OUT.mkdir(exist_ok=True)
p=ROOT/'validation/serviceable_torso_v2';r=json.loads((p/'report.json').read_text());ss=cq.importers.importStep(str(p/'assembly.step')).val().Solids();assert len(ss)==len(r['parts'])
parts={row['name']:s for row,s in zip(r['parts'],ss)}
plan={'candidate':'NBK SLH-M3-8 x4','head_diameter_mm':5.5,'head_height_mm':2,'length_mm':8,'seat_x_mm':48.3,'head_recess_diameter_mm':6,'recess_x_mm':[46.3,48.3],'Tab5_nominal_back_x_mm':52,'nominal_penetration_mm':4.3,'criteria':'Flag interference above0.01mm3 against other nominal parts; Tab5 thread envelope recorded separately, not pass','stop':'One8mm candidate; no blind-depth inference from mesh or M3*10 annotation'}
(OUT/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
carrier=parts['new_carrier']
for y in [-60,60]:
 for z in [52,124]:
  recess=cq.Solid.makeCylinder(3,2,cq.Vector(46.3,y,z),cq.Vector(1,0,0))
  carrier=carrier.cut(recess)
carrier=carrier.clean();assert carrier.isValid() and len(carrier.Solids())==1
parts['new_carrier']=carrier
cq.exporters.export(carrier,str(OUT/'carrier_installed_approximation.step'))
rows=[];screws=[]
for y in [-60,60]:
 for z in [52,124]:
  shaft=cq.Solid.makeCylinder(1.5,8,cq.Vector(48.3,y,z),cq.Vector(1,0,0));head=cq.Solid.makeCylinder(2.75,2,cq.Vector(46.3,y,z),cq.Vector(1,0,0));screw=shaft.fuse(head)
  name=f'frame_screw_{y}_{z}';cq.exporters.export(screw,str(OUT/(name+'.step')));screws.append(screw)
  hits=[]
  for n,s in parts.items():
   if n=='Tab5':continue
   vol=screw.intersect(s).Volume()
   if vol>.01:hits.append({'part':n,'overlap_mm3':vol})
  rows.append({'name':name,'unexpected_overlaps':hits,'head_gap_to_fixed_shell_mm':head.distance(parts['new_fixed_shell']),
               'simplified_Tab5_overlap_mm3':screw.intersect(parts['Tab5']).Volume()})
result={'carrier_valid':carrier.isValid(),'carrier_solids':len(carrier.Solids()),'carrier_removed_volume_mm3':next(x['volume_mm3'] for x in r['parts'] if x['name']=='new_carrier')-carrier.Volume(),'rows':rows,'all_other_parts_clear':all(not row['unexpected_overlaps'] for row in rows),
 'candidate_added_mass_g':4*.62,'thread_engagement_qualified':False,'mount_torque_qualified':False,
 'screw_length_condition':'Usable female depth >=4.3mm plus tip/bottom/tolerance allowance; minimum effective thread engagement must also be specified',
 'thread_envelope_note':'CAD clearance radius1.45 smaller than M3 major radius1.5; do not treat Tab5 overlap as real thread collision or verified engagement',
 'source_sha256':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [p/'report.json',p/'assembly.step']},'manufacturing_release':False}
(OUT/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
