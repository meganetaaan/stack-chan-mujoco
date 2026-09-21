"""Compare externally accessible nut on filled boss, without full assembly certification."""
import argparse,json
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
plan={'question':'Does placing the nut above the boss remove captive-cavity assembly dependence within the existing boot?','nut_bottom_z_mm':-11.6,'screw_length_mm':10,'tool_envelope':'radius4 cylinder from z=-11.59 to +8.41; space reservation, not selected tool','criteria':{'overlap_max_mm3':.01,'single_valid_parts':True},'stop_condition':'One external-nut candidate, both sides; preserve failure','limitations':['Tool reservation only','Full robot and motion not included','Preload creep thread engagement and strength unverified']};(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');rows=[]
for side,cy in [('left',6),('right',-6)]:
 root=Path('validation/sole_wide_seat_v1/cad');base=cq.importers.importStep(str(root/f'{side}_yoke.step')).val();boot=cq.importers.importStep(f'validation/boot_low_head_candidate_v1/cad/{side}_boot_shell.step').val()
 def cyl(r,z,h):return cq.Solid.makeCylinder(r,h,cq.Vector(35,cy,z))
 y=base.fuse(cq.Solid.makeBox(4.42,4.42,1.82,cq.Vector(32.79,cy-2.21,-14.21))).cut(cyl(1.15,-19.01,7.42)).clean()
 nut=cq.importers.importStep(str(root/f'{side}_nut.step')).val().translate((0,0,2.6))
 screw=cyl(1,-19.9,10).fuse(cyl(1.9,-21.2,1.3)).clean()
 tool=cyl(4,-11.59,20)
 overlaps={'nut_boot':nut.intersect(boot).Volume(),'nut_yoke':nut.intersect(y).Volume(),'screw_boot':screw.intersect(boot).Volume(),'screw_yoke':screw.intersect(y).Volume(),'tool_boot':tool.intersect(boot).Volume(),'tool_yoke':tool.intersect(y).Volume()}
 objects={'yoke':y,'nut':nut,'screw':screw};valid=all(s.isValid() and len(s.Solids())==1 for s in objects.values())
 for name,s in objects.items():cq.exporters.export(s,str(a.out/f'{side}_{name}.step'))
 rows.append({'side':side,'valid_parts':valid,'overlap_mm3':overlaps,'nominal_geometry_gate':valid and max(overlaps.values())<=.01,'added_yoke_volume_mm3':y.Volume()-base.Volume()})
report={'rows':rows,'manufacturing_release':False,'strength_verified':False};(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
