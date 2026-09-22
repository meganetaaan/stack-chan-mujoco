"""Bounded LB-020 substitution screen at current battery center; no layout optimization."""
import hashlib,itertools,json
from pathlib import Path
import cadquery as cq
ROOT=Path(__file__).resolve().parents[3]
out=ROOT/'validation/protected_battery_fit_v1';out.mkdir(exist_ok=True)
p=ROOT/'validation/torso_power_integration_v2'
report=json.loads((p/'report.json').read_text())
solids=cq.importers.importStep(str(p/'torso_candidate.step')).val().Solids()
parts=dict(zip([r['name'] for r in report['parts']],solids));assert len(parts)==100
b=parts.pop('battery').BoundingBox();center=[(getattr(b,k+'min')+getattr(b,k+'max'))/2 for k in 'xyz']
plan={'candidate':'ROBOTIS LB-020','size_mm':[70,36,24],'mass_g':102,'source':'https://robotis.us/products/lipo-battery-11-1v-1300mah-lb-020',
 'predeclared_scope':'Six axis-aligned orientations at unchanged battery center against all99 other torso parts',
 'overlap_flag_mm3':.01,'stop':'No tray modification or free placement search in this screen',
 'limits':['Nominal box excludes cables/connectors/swelling/tolerances','Fixed torso, no legs or dynamic sweep','Fit is not retention or electrical qualification']}
(out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
rows=[]
for dims in itertools.permutations(plan['size_mm']):
 box=cq.Workplane('XY').box(*dims).translate(tuple(center)).val();hits=[]
 for n,s in parts.items():
  a,t=box.BoundingBox(),s.BoundingBox()
  if any(getattr(a,k+'max')<=getattr(t,k+'min') or getattr(t,k+'max')<=getattr(a,k+'min') for k in 'xyz'):continue
  v=box.intersect(s).Volume()
  if v>plan['overlap_flag_mm3']:hits.append({'part':n,'overlap_mm3':v})
 other_gap=min(box.distance(s) for n,s in parts.items() if n!='tray') if all(h['part']=='tray' for h in hits) else None
 rows.append({'dimensions_xyz_mm':dims,'overlaps':hits,'nominal_overlap_free':not hits,'min_gap_excluding_existing_tray_mm':other_gap})
result={'source_sha256':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [p/'report.json',p/'torso_candidate.step']},'center_mm':center,'old_battery_bbox_mm':[getattr(b,k+'len') for k in 'xyz'],'rows':rows,'manufacturing_release':False}
(out/'report.json').write_text(json.dumps(result,indent=2)+'\n')
print([(x['dimensions_xyz_mm'],[h['part'] for h in x['overlaps']]) for x in rows])
