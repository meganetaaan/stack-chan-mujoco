"""Raise retention heads internally to compare axial fit without changing sole height."""
import argparse,json,hashlib
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
positions=json.loads(Path('validation/keyhole_front18_v1/retention/plan.json').read_text())['positions_relative_center_mm'];rows=[]
for side,cy in [('left',6),('right',-6)]:
 src=Path(f'validation/sole_contact_split_v1/{side}_holder_envelope.step');s=cq.importers.importStep(str(src)).val();before=s.Volume()
 for x,dy in positions:
  y=cy+dy
  s=s.cut(cq.Solid.makeCylinder(4.01,1.51,cq.Vector(x,y,-15.8)))
  s=s.fuse(cq.Solid.makeCylinder(2.8,.42,cq.Vector(x,y,-15.81)))
  s=s.fuse(cq.Solid.makeCylinder(4,1.5,cq.Vector(x,y,-15.4)))
 s=s.clean();assert s.isValid() and len(s.Solids())==1
 cq.exporters.export(s,str(a.out/f'{side}_holder_envelope.step'))
 yoke=cq.importers.importStep(f'validation/rigid_sole_keyhole_v1/{side}_yoke.step').val();boot=cq.importers.importStep(f'validation/boot_low_head_candidate_v1/cad/{side}_boot_shell.step').val()
 rows.append({'side':side,'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'volume_delta_mm3':s.Volume()-before,'boot_overlap_mm3':s.intersect(boot).Volume(),'yoke_overlap_mm3':s.intersect(yoke).Volume(),'valid_single_solid':True})
(a.out/'report.json').write_text(json.dumps({'rows':rows,'head_raise_mm':.4,'head_bottom_z_mm':-15.4,'head_top_z_mm':-13.9,'axial_nominal_gap_mm':.6,'boundary_error_each_comparison_mm':.2,'axial_worst_comparison_mm':.2,'manufacturing_release':False,'scope':'Aligned nominal geometry and provisional clearance arithmetic only'},indent=2)+'\n');print(json.dumps(rows))
