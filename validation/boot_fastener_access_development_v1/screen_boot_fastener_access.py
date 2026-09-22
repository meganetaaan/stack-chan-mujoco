"""Screen axial access to boot mounting holes before selecting a fastener stack."""
import argparse,hashlib,json
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[3]
if a.out.exists():p.error('new output required')
a.out.mkdir(parents=True)
paths={s:{'boot':root/f'validation/boot_seats_development_v1/{s}_boot_shell.step','yoke':root/f'validation/native_horn_yoke_development_v1/v4/{s}_foot_yoke.step','sole':root/f'software/sim/mujoco/assets/r9_fast_turn_v1/cad/{s}_sole_TPU.step'} for s in ('left','right')}
plan={'scope':__doc__,'assumed_tool_radius_mm':2.5,'upper_tool_z_mm':[-12.59,40],'lower_tool_z_mm':[-35,-19.01],'through_hole_radius_mm':1,'through_hole_z_mm':[-19,-12.6],'overlap_limit_mm3':.01,'source_sha256':{str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for row in paths.values() for f in row.values()},'limitations':['Tool envelope is an explicit 5 mm diameter screening assumption, not a selected driver specification.','Sole removal order, screw head, nut, washer, tolerance, insertion and tightening strength are not qualified.']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');rows=[]
for side,files in paths.items():
 shapes={k:cq.importers.importStep(str(v)).val() for k,v in files.items()};sign=1 if side=='left' else -1
 for x in (-34,36):
  for y in (sign*6-20.5,sign*6+20.5):
   for mode,r,z0,z1 in [('upper_tool',2.5,-12.59,40),('lower_tool',2.5,-35,-19.01),('shaft',1,-19,-12.6)]:
    tool=cq.Solid.makeCylinder(r,z1-z0,cq.Vector(x,y,z0));overlaps={name:tool.intersect(shape).Volume() for name,shape in shapes.items()}
    rows.append({'side':side,'xy_mm':[x,y],'mode':mode,'overlap_mm3':overlaps,'passed':all(v<=.01 for v in overlaps.values())})
report={'rows':rows,'all_access_pass':all(r['passed'] for r in rows),'manufacturing_release':False}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'failed_rows':[r for r in rows if not r['passed']],'all_access_pass':report['all_access_pass']},indent=2))
