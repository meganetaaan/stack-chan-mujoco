import cadquery as cq,json
from pathlib import Path
rows=[]
for side,sign in [('left',1),('right',-1)]:
 b=cq.importers.importStep(f'validation/boot_low_head_candidate_v1/cad/{side}_boot_shell.step').val()
 for x in (-34,36):
  for y in (sign*6-20.5,sign*6+20.5):
   rows.append({'side':side,'xy_mm':[x,y],'tip_extension_to_z_minus12_overlap_mm3':b.intersect(cq.Solid.makeCylinder(1,1.4,cq.Vector(x,y,-13.4))).Volume(),'central_roof_probe_overlap_mm3':b.intersect(cq.Solid.makeCylinder(1,.8,cq.Vector(x,y,-12.8))).Volume()})
print(json.dumps(rows))
Path('validation/boot_tip_relief_v1/original_tip_probe.json').write_text(json.dumps(rows,indent=2)+'\n')
