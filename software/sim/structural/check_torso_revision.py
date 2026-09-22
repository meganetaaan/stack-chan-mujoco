"""Verify that torso v2 changes only the two intended bracket bores."""
import hashlib,json
from pathlib import Path
import cadquery as cq
roots=[Path('validation/torso_power_integration_v1'),Path('validation/torso_power_integration_v2')]
sets=[];files=[]
for root in roots:
 rp=root/'report.json';sp=root/'torso_candidate.step';files += [rp,sp]
 r=json.loads(rp.read_text());ss=cq.importers.importStep(str(sp)).val().Solids();assert len(ss)==len(r['parts'])==100
 shapes={}
 for item,shape in zip(r['parts'],ss):
  assert abs(item['volume_mm3']-shape.Volume())<1e-5
  shapes[item['name']]=shape
 sets.append(shapes)
assert sets[0].keys()==sets[1].keys()
rows=[]
for n,new in sets[1].items():
 old=sets[0][n];added=new.cut(old).Volume();removed=old.cut(new).Volume()
 expected=n in ['power__left_bracket','power__right_bracket']
 assert added<1e-6
 assert removed>18 if expected else removed<1e-6
 rows.append({'part':n,'added_volume_mm3':added,'removed_volume_mm3':removed,'expected_change':expected})
report={'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},'rows':rows,
 'unchanged_parts':98,'subset_changed_parts':2,
 'interpretation':'Existing nominal external rigid clearances cannot decrease by these material removals. Strength and seat geometry do not inherit this result.',
 'manufacturing_release':False}
(roots[1]/'revision_check.json').write_text(json.dumps(report,indent=2)+'\n')
print('100part comparison:98 unchanged,2 material-removal-only changes')
