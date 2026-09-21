"""Compare larger rigid-sole keyholes without changing the outer foot envelope."""
import argparse,json,hashlib
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
positions=json.loads(Path('validation/keyhole_front18_v1/retention/plan.json').read_text())['positions_relative_center_mm'];rows=[]
for side,cy in [('left',6),('right',-6)]:
 src=Path(f'validation/sole_external_nut_v1/{side}_yoke.step');old=cq.importers.importStep(str(src)).val();s=old
 for x,dy in positions:
  y=cy+dy
  entry=cq.Solid.makeCylinder(4.6,3.02,cq.Vector(x+8,y,-19.01))
  slot=cq.Solid.makeBox(8,6.8,3.02,cq.Vector(x,y-3.4,-19.01))
  stem=cq.Solid.makeCylinder(3.4,3.02,cq.Vector(x,y,-19.01))
  s=s.cut(entry.fuse(slot).fuse(stem))
 s=s.clean();assert s.isValid() and len(s.Solids())==1
 cq.exporters.export(s,str(a.out/f'{side}_yoke.step'))
 rows.append({'side':side,'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'removed_mm3':old.Volume()-s.Volume(),'valid_single_solid':True})
r={'rows':rows,'entry_radius_mm':4.6,'slot_half_width_mm':3.4,'stem_radius_mm':2.8,'head_radius_mm':4,'nominal_radial_gap_mm':.6,'nominal_head_slot_overlap_mm':.6,'unchanged_axial_gap_mm':.2,'under_previous_boundary_error_each_mm':.2,'radial_gap_comparison_mm':.2,'head_slot_overlap_comparison_mm':.2,'axial_gap_comparison_mm':-.2,'decision':'Radial improvement only; axial fit and reduced retention ligament remain unresolved','manufacturing_release':False}
(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
