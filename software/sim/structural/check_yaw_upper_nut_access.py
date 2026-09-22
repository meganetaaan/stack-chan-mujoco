"""Compare existing nut-driver reservation against v5/v6 support solids."""
import argparse,hashlib,json
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
plan={'question':'Does upper reinforcement obstruct the existing axial nut-driver reservation?', 'tool':'Existing comparison envelope radius4 mm, starts Z91.9, length50; tip cavity radius2.9 depth8. Not a qualified purchased tool.', 'criterion':'No added tool/support overlap above0.01 mm3; actual selected tool and operating clearance remain separate.', 'stop':'Eight axes, v5/v6 support only. No radius optimization or CAD changes.'}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');rows=[];hashes={}
for side,cy in [('left',26),('right',-26)]:
 paths={'v5':Path(f'validation/yaw_crossweb_screw_relief_v1/{side}_yaw_fixed_support.step'),'v6':Path(f'validation/yaw_upper_shelf_v1/{side}_yaw_fixed_support.step')}
 shapes={v:cq.importers.importStep(str(f)).val() for v,f in paths.items()};hashes.update({str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in paths.values()})
 for x in [-34,8.1]:
  for y in [cy-10,cy+10]:
   tool=cq.Solid.makeCylinder(4,50,cq.Vector(x,y,91.9)).cut(cq.Solid.makeCylinder(2.9,8,cq.Vector(x,y,91.9)))
   overlaps={v:tool.intersect(s).Volume() for v,s in shapes.items()}
   rows.append({'side':side,'x_mm':x,'y_mm':y,'overlap_mm3':overlaps,'new_obstruction':overlaps['v6']-overlaps['v5']>.01})
r={'rows':rows,'new_obstructions':sum(x['new_obstruction'] for x in rows),'source_sha256':hashes,'assembly_verified':False,'manufacturing_release':False};(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
