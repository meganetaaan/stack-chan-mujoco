"""Check certificate interval coverage and aggregate bounds, without re-solving CAD."""
import argparse,collections,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('directory',type=Path);a=p.parse_args();root=a.directory
r=json.loads((root/'report.json').read_text());plan=json.loads((root/'plan.json').read_text());assert r['continuous_nominal_route_verified'] and len(r['segments'])==3
methods=collections.Counter();bounds=[];contacts=[];leaves=0
for seg in r['segments']:
 assert len(seg['checks'])==45*39 and seg['pass_nominal']
 u,v=seg['start_mm'],seg['end_mm'];axis=next(i for i in range(3) if u[i]!=v[i])
 for c in seg['checks']:
  assert c['pass_nominal'];methods[c['method']]+=1
  if c['method']=='contact_halfspace':
   assert c['x_separation_mm']>=-plan['criteria']['cad_numerical_allowance_mm'];contacts.append(c['x_separation_mm'])
  elif c['method']=='adaptive_translation_distance':
   assert c['failure'] is None;intervals=[]
   for leaf in c['certified_intervals']:
    assert leaf['lower_bound_mm']>=plan['criteria']['minimum_unintended_gap_mm'];bounds.append(leaf['lower_bound_mm']);leaves+=1
    assert all(leaf['start'][i]==leaf['end'][i]==u[i] for i in range(3) if i!=axis)
    intervals.append(sorted([leaf['start'][axis],leaf['end'][axis]]))
   intervals.sort();assert abs(intervals[0][0]-min(u[axis],v[axis]))<1e-9 and abs(intervals[-1][1]-max(u[axis],v[axis]))<1e-9
   assert all(abs(x[1]-y[0])<1e-9 for x,y in zip(intervals,intervals[1:]))
   assert abs(sum(y-x for x,y in intervals)-abs(v[axis]-u[axis]))<1e-9
  else:
   assert c['lower_bound_mm']>=plan['criteria']['minimum_unintended_gap_mm'];bounds.append(c['lower_bound_mm'])
summary={'segment_pair_checks':sum(methods.values()),'methods':dict(methods),'minimum_certified_unintended_clearance_mm':min(bounds),'minimum_contact_halfspace_separation_mm':min(contacts),'adaptive_pairs':methods['adaptive_translation_distance'],'adaptive_leaf_intervals':leaves,'coverage_no_gaps_or_overlaps':True,'scope':'Nominal route certificate consistency; not independent CAD re-solve or production qualification'}
(root/'certificate_audit.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
