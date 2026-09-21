"""Local boot screw-tip relief; preserve clamped nut bearing surface."""
import argparse, hashlib, json
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--out',type=Path,required=True)
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
plan={'radius_mm':1.6,'bottom_z_mm':-12.81,'top_z_mm':-12.0,
 'basis':'0.8 mm deeper than old cavity roof; allows 0.6 mm axial clearance after existing +/-0.2 mm printed boundary error, before purchased screw length tolerance.',
 'criteria':['single valid solid','no added material','nut bearing region unchanged'],
 'limits':['Comparison geometry, not selected final hole diameter or depth','Screw diameter and length tolerances unknown','Nut thread engagement remains marginal','Local roof thickness is geometric, not strength approval']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
rows=[]
for side,sign in [('left',1),('right',-1)]:
 src=Path(f'validation/boot_low_head_candidate_v1/cad/{side}_boot_shell.step')
 old=cq.importers.importStep(str(src)).val();new=old
 for x in (-34,36):
  for y in (sign*6-20.5,sign*6+20.5):
   new=new.cut(cq.Solid.makeCylinder(1.6,.81,cq.Vector(x,y,-12.81)))
 new=new.clean()
 bearing_region=cq.Workplane('XY').box(200,200,100).val().translate((0,0,-64.6))
 bearing_change=old.cut(new).intersect(bearing_region).Volume()
 probes=[]
 for x in (-34,36):
  for y in (sign*6-20.5,sign*6+20.5):
   probe=cq.Solid.makeCylinder(.01,50,cq.Vector(x,y,-12))
   intervals=sorted([[s.BoundingBox().zmin,s.BoundingBox().zmax] for s in new.intersect(probe).Solids()])
   probes.append({'xy_mm':[x,y],'axis_material_intervals_above_relief_mm':intervals})
 assert new.isValid() and len(new.Solids())==1 and bearing_change<1e-8
 assert new.cut(old).Volume()<1e-8
 cq.exporters.export(new,str(a.out/f'{side}_boot_shell.step'))
 rows.append({'side':side,'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'removed_mm3':old.Volume()-new.Volume(),'bearing_region_change_mm3':bearing_change,'axis_probes':probes,'single_valid_solid':True})
(a.out/'report.json').write_text(json.dumps({'rows':rows,'manufacturing_release':False},indent=2)+'\n')
print(json.dumps(rows))
