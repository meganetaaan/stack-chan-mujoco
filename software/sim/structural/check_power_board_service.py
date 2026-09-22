"""Check straight service sweeps after adding the provisional power board reservation."""
import argparse,hashlib,json
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
pack=json.loads(Path('board/mechanical/prototype/power_packaging_revA/report.json').read_text())
paths=list(pack['sources_sha256']);shapes={path:cq.importers.importStep(path).val() for path in paths}
boardpaths=['validation/power_board_reservation_v3/'+n+'.step' for n in ('board','components')]
boardparts={path:cq.importers.importStep(path).val() for path in boardpaths}
tab=next(p for p in paths if p.endswith('/Tab5.step'));battery=next(p for p in paths if p.endswith('/battery_candidate.step'));strap=next(p for p in paths if p.endswith('/strap_envelope.step'))
def prism(s,travel):
 b=s.BoundingBox();return cq.Solid.makeBox(b.xlen+travel,b.ylen,b.zlen,cq.Vector(b.xmin,b.ymin,b.zmin))
# Predefined acceptance is nominal no intersection; other service qualifications excluded.
plan={'direction':'+X','criteria':'No swept nominal volume intersection for stated included obstacles','cases':['Tab5 against new board only','Battery against new board only after Tab5/strap removal','New board against current packaging after Tab5 removal'],'limits':['Existing service-path checks remain separate','Fasteners, connectors, cables and hand/tool space not included','Board reservation is not a routed/mounted assembly']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
rows=[]
for name,path in [('Tab5',tab),('battery',battery)]:
 s=shapes[path];travel=69-s.BoundingBox().xmin;sweep=prism(s,travel)
 cq.exporters.export(sweep,str(a.out/(name+'_sweep.step')))
 for bp,t in boardparts.items():rows.append({'moving':name,'obstacle':bp,'travel_mm':travel,'overlap_mm3':sum(sweep.intersect(z).Volume() for z in t.Solids()),'distance_mm':sweep.distance(t)})
for bp,s in boardparts.items():
 travel=69-s.BoundingBox().xmin;sweep=prism(s,travel)
 cq.exporters.export(sweep,str(a.out/(Path(bp).stem+'_removal_sweep.step')))
 for path,t in shapes.items():
  if path==tab:continue
  rows.append({'moving':bp,'obstacle':path,'travel_mm':travel,'overlap_mm3':sum(sweep.intersect(z).Volume() for z in t.Solids()),'distance_mm':min(sweep.distance(z) for z in t.Solids())})
r={'checks':rows,'nominal_added_service_paths_clear':all(x['overlap_mm3']<1e-6 for x in rows),'sources_sha256':{p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in paths+boardpaths},'physical_service_qualified':False}
(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print('paths_clear',r['nominal_added_service_paths_clear']);print('collisions',[x for x in rows if x['overlap_mm3']>=1e-6]);print('min_gap',min(x['distance_mm'] for x in rows))
