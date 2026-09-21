"""Check changed-pair overlap growth while retaining existing overlap evidence."""
import argparse,hashlib,itertools,json
from pathlib import Path
import cadquery as cq
import numpy as np
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate',type=Path,required=True);a=p.parse_args()
plan={'scope':'All pairs with at least one of the 12 changed components; compare nominal overlap volume to revB.','criterion_added_overlap_mm3':.01,'limits':['Existing overlap is reported, not qualified as intentional.','Zero new volume does not prove tolerances, assembly access or strength.']}
(a.candidate/'overlap_plan.json').write_text(json.dumps(plan,indent=2)+'\n')
def read(folder):
 inv=json.loads((folder/'inventory.json').read_text())['parts'];mom=json.loads((folder/'geometric_moments.json').read_text())['parts'];solids=cq.importers.importStep(str(folder/'yaw_support_candidate.step')).val().Solids()
 assert len(inv)==len(solids)==len(mom)==52
 for item,prop,solid in zip(inv,mom,solids):
  assert item['name']==prop['name'] and abs(item['volume_mm3']-solid.Volume())<1e-5
  assert np.allclose(np.array(solid.Center().toTuple())*.001,prop['com_assembly_m'],atol=1e-8,rtol=0)
 return {item['name']:solid for item,solid in zip(inv,solids)}
base=Path('board/mechanical/prototype/yaw_support_candidate/revB');old=read(base);new=read(a.candidate)
changes={r['name'] for r in json.loads((a.candidate/'change_accounting.json').read_text())['changed_parts']}
def overlap(s,t):
 b,c=s.BoundingBox(),t.BoundingBox()
 if any(min(getattr(b,k+'max'),getattr(c,k+'max'))-max(getattr(b,k+'min'),getattr(c,k+'min'))<=1e-7 for k in 'xyz'):return 0.
 return s.intersect(t).Volume()
rows=[];tested=0
for x,y in itertools.combinations(new,2):
 if x not in changes and y not in changes:continue
 tested+=1;before=overlap(old[x],old[y]);after=overlap(new[x],new[y]);delta=after-before
 if max(before,after)>.000001:rows.append({'pair':[x,y],'old_overlap_mm3':before,'new_overlap_mm3':after,'increase_mm3':delta,'increase_flag':delta>.01})
paths=[base/'yaw_support_candidate.step',a.candidate/'yaw_support_candidate.step']
result={'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},'part_order_volume_and_com_checked':True,'pairs_tested':tested,'nonzero_pairs':rows,'new_overlap_flags':[r for r in rows if r['increase_flag']],'full_assembly_qualified':False}
(a.candidate/'overlap_report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'pairs':tested,'nonzero':len(rows),'flags':len(result['new_overlap_flags'])}))
