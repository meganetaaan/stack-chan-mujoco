"""Post-print boot nut insertion without cutting the nut bearing floor."""
import argparse,hashlib,json
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
plan={'question':__doc__,'slot_width_mm':4.4,'slot_z_mm':[-14.6,-12.8],'nut_envelope_mm':[4,4,1.2],
 'criteria':{'single_valid_solid':True,'bearing_floor_removed_volume_max_mm3':1e-8,'continuous_swept_overlap_max_mm3':.01},
 'stop':'One slot geometry at eight positions; preserve failed results instead of iterative widening.',
 'limits':['Nominal envelope; actual nut and print tolerances unqualified','Installed screw retains nut; loose nut may exit','Tool grip space not modeled','Removed side wall changes stiffness and needs structural evaluation']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
rows=[]
for side,sign in [('left',1),('right',-1)]:
 src=Path(f'validation/boot_low_head_candidate_v1/cad/{side}_boot_shell.step')
 old=cq.importers.importStep(str(src)).val();new=old;cy=sign*6
 for x in (-34,36):
  for direction in (-1,1):
   y=cy+direction*20.5;outside=cy+direction*30
   lo,hi=sorted([y,outside])
   new=new.cut(cq.Solid.makeBox(4.4,hi-lo+2.2,1.8,cq.Vector(x-2.2,lo-(2.2 if direction>0 else 0),-14.6)))
 new=new.clean();valid=new.isValid() and len(new.Solids())==1
 # All material below the nut seating plane must be unchanged.
 below=cq.Solid.makeBox(200,200,100,cq.Vector(-100,-100,-114.6))
 floor_change=old.cut(new).intersect(below).Volume()
 paths=[]
 for x in (-34,36):
  for direction in (-1,1):
   y=cy+direction*20.5;outside=cy+direction*30;lo,hi=sorted([y,outside])
   swept=cq.Solid.makeBox(4,hi-lo+4,1.2,cq.Vector(x-2,lo-2,-14.6))
   overlap=swept.intersect(new).Volume()
   paths.append({'xy_mm':[x,y],'outside_y_mm':outside,'continuous_swept_overlap_mm3':overlap})
 cq.exporters.export(new,str(a.out/f'{side}_boot_shell.step'))
 rows.append({'side':side,'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'single_valid_solid':valid,'removed_volume_mm3':old.Volume()-new.Volume(),'bearing_floor_removed_volume_mm3':floor_change,'paths':paths,'nominal_gate':valid and floor_change<1e-8 and all(r['continuous_swept_overlap_mm3']<=.01 for r in paths)})
(a.out/'report.json').write_text(json.dumps({'rows':rows,'manufacturing_release':False,'strength_verified':False},indent=2)+'\n')
print(json.dumps(rows))
