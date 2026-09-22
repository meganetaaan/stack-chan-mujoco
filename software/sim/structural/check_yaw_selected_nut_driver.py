"""Compare selected catalog blade envelope against original and relieved upper supports."""
import argparse,hashlib,json
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
plan={'question':'Does upper reinforcement obstruct the existing axial nut-driver reservation?', 'tool':'Wera05118120001 catalog blade diameter5.7 length60, bottomZ91.9; filled cylinder for support-only test. Handle and socket fit excluded.', 'criterion':'Blade/support distance>=0.9 mm from existing nominal clearance budget; tool tolerance and hand access not qualified.', 'stop':'Eight axes, original/relieved support only. No radius optimization or CAD changes.'}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');rows=[];hashes={}
for side,cy in [('left',26),('right',-26)]:
 paths={'original_upper':Path(f'validation/yaw_upper_shelf_v1/{side}_yaw_fixed_support.step'),'relieved_upper':Path(f'validation/yaw_upper_tool_relief_v1/{side}_yaw_fixed_support.step')}
 shapes={v:cq.importers.importStep(str(f)).val() for v,f in paths.items()};hashes.update({str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in paths.values()})
 for x in [-34,8.1]:
  for y in [cy-10,cy+10]:
   tool=cq.Solid.makeCylinder(2.85,60,cq.Vector(x,y,91.9))
   overlaps={v:tool.intersect(s).Volume() for v,s in shapes.items()}
   rows.append({'side':side,'x_mm':x,'y_mm':y,'overlap_mm3':overlaps,'new_obstruction':overlaps['relieved_upper']>.01,'distances_mm':{v:tool.distance(s) for v,s in shapes.items()},'relieved_blade_clearance_pass':tool.distance(shapes['relieved_upper'])>=.9})
r={'rows':rows,'new_obstructions':sum(x['new_obstruction'] for x in rows),'source_sha256':hashes,'assembly_verified':False,'manufacturing_release':False};(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
