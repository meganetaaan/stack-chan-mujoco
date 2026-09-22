"""Six axial translation probes for nut covers; not arbitrary-rotation capture proof."""
import hashlib,json
from pathlib import Path
import cadquery as cq
ROOT=Path(__file__).resolve().parents[3];out=ROOT/'validation/nut_cover_capture_v1';out.mkdir(exist_ok=True)
plan={'probe_distance_mm':1,'intersection_threshold_mm3':1e-6,'directions':['+X','-X','+Y','-Y','+Z','-Z'],'criterion':'Each1mm axis translation intersects a physical stop in nominal geometry','stop':'24 probes; no rigid-body search or elastic retention claim','limits':['Tab5 simplified source geometry','No rotational escape or tolerance/deflection proof','No loads/strength']}
(out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
p=ROOT/'validation/carrier_nut_covers_v2';q=ROOT/'validation/serviceable_torso_v1';files=[p/'carrier.step',q/'assembly.step',q/'report.json'];carrier=cq.importers.importStep(str(files[0])).val();r=json.loads((q/'report.json').read_text());ss=cq.importers.importStep(str(q/'assembly.step')).val().Solids();assert len(ss)==len(r['parts'])==111
parts=dict(zip([x['name'] for x in r['parts']],ss));obstacles={'carrier':carrier,'Tab5':parts['Tab5']};rows=[]
for sign in [-1,1]:
 for z in [88,112]:
  f=p/f'cover_{sign}_{z}.step';files.append(f);cap=cq.importers.importStep(str(f)).val()
  for axis in range(3):
   for direction in [-1,1]:
    v=[0,0,0];v[axis]=direction;shifted=cap.translate(tuple(v));hits=[]
    for n,s in obstacles.items():
     volume=shifted.intersect(s).Volume()
     if volume>1e-6:hits.append({'part':n,'overlap_mm3':volume})
    rows.append({'cover':f.stem,'direction':'XYZ'[axis]+('+' if direction>0 else '-'),'probe_translation_mm':v,'blocking_parts':hits,'axial_probe_blocked':bool(hits)})
result={'cases':rows,'all_axial_probes_blocked':all(x['axial_probe_blocked'] for x in rows),'source_sha256':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},'arbitrary_motion_capture_proven':False,'manufacturing_release':False}
(out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps([(x['cover'],x['direction'],[h['part'] for h in x['blocking_parts']]) for x in rows]))
