"""Candidate sole clamp washer replacing the bypass spacer; strength unqualified."""
import argparse,json,hashlib
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False);rows=[]
for side,cy in [('left',6),('right',-6)]:
 src=Path(f'validation/rigid_sole_heads_v1/{side}_holder_envelope.step');old=cq.importers.importStep(str(src)).val()
 def cyl(r,z,h):return cq.Solid.makeCylinder(r,h,cq.Vector(35,cy,z))
 holder=old.fuse(cyl(3.21,-19.6,.6)).cut(cyl(1.15,-19.61,.62)).clean()
 washer=cyl(3,-19.9,.3).cut(cyl(1.15,-19.91,.32)).clean()
 assert holder.isValid() and len(holder.Solids())==1 and washer.isValid()
 cq.exporters.export(holder,str(a.out/f'{side}_holder_envelope.step'));cq.exporters.export(washer,str(a.out/f'{side}_clamp_washer.step'))
 fixed={'washer':washer,'yoke':cq.importers.importStep(f'validation/rigid_sole_keyhole_v1/{side}_yoke.step').val(),'screw':cq.importers.importStep(f'validation/sole_external_nut_v1/{side}_screw.step').val(),'boot':cq.importers.importStep(f'validation/boot_low_head_candidate_v1/cad/{side}_boot_shell.step').val()}
 rows.append({'side':side,'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'holder_volume_delta_mm3':holder.Volume()-old.Volume(),'aligned_overlap_mm3':{n:holder.intersect(s).Volume() for n,s in fixed.items()},'washer_screw_overlap_mm3':washer.intersect(fixed['screw']).Volume(),'holder_down_0_05_washer_overlap_mm3':holder.translate((0,0,-.05)).intersect(washer).Volume(),'seat_annular_area_mm2':3.141592653589793*(3**2-1.15**2)})
(a.out/'report.json').write_text(json.dumps({'rows':rows,'washer_candidate_dimensions_mm':{'OD':6,'ID':2.3,'thickness':.3},'washer_status':'Custom geometry candidate, not selected manufactured part','polymer_seat_nominal_thickness_mm':.6,'head_floor_nominal_clearance_mm':.8,'removed_part':'Old 0.9mm bypass spacer','manufacturing_release':False,'strength_qualified':False},indent=2)+'\n');print(json.dumps(rows))
