"""Check native-horn yoke against every manufacturer servo component at neutral."""
import argparse,hashlib,json
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[3]
if a.out.exists():p.error('new output required')
a.out.mkdir(parents=True)
step=root/'validation/x330_manufacturer_cad_v1/XL_XC_330.stp'
mapping=root/'validation/x330_component_map_v1/report.json';meta=json.loads(mapping.read_text())
if hashlib.sha256(step.read_bytes()).hexdigest()!=meta['source_sha256']:raise ValueError('component mapping source mismatch')
solids=cq.importers.importStep(str(step)).val().Solids()
if len(solids)!=len(meta['components']):raise ValueError('component count mismatch')
parts=[s.rotate((0,0,0),(-1,1,-1),120).translate((-3.5,0,0)) for s in solids]
yoke_dir=root/'validation/native_horn_yoke_development_v1/v4'
plan=dict(scope=__doc__,overlap_limit_mm3=.01,intended_horn_contact_indices=[3,10],
          source_sha256={str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [step,mapping,*yoke_dir.glob('*.step')]},
          limitations=['Neutral pose only','Manufacturer screws are assembly CAD, not approved purchased screw lengths','New frame-to-horn M2 fasteners not yet included','Cap rotation assignment and mating contact not yet qualified'])
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
rows=[]
for side in ('left','right'):
 yoke=cq.importers.importStep(str(yoke_dir/f'{side}_foot_yoke.step')).val()
 for i,part in enumerate(parts):
  d=float(yoke.distance(part));volume=float(yoke.intersect(part).Volume()) if d<1e-6 else 0
  rows.append(dict(side=side,component_index=i,product_name=meta['components'][i]['product_name'],distance_mm=d,overlap_mm3=volume,
                   intended_surface_contact=i in (3,10),overlap_pass=volume<=.01))
report=dict(rows=rows,overlap_findings=[r for r in rows if not r['overlap_pass']],manufacturing_release=False)
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['overlap_findings'],indent=2))
