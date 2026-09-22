"""Raise upper crossbar to clear the manufacturer case without thinning it."""
import argparse,hashlib,json
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[3]
if a.out.exists():p.error('new output required')
a.out.mkdir(parents=True)
source=root/'validation/ankle_gimbal_relief_development_v1/v4/cad'
plan=dict(scope=__doc__,bridge_x_mm=[-46,-38],old_z_mm=[14,16.4],new_z_mm=[14.9,17.3],nominal_case_clearance_mm=.4,
          criteria={'valid_single_solid':True,'bridge_thickness_mm':2.4},
          limitations=['Case fastening and load path unresolved','New outer sweep must be verified; 0.4 mm case gap alone is not full clearance acceptance'])
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');rows=[]
for side,sign in [('left',1),('right',-1)]:
 path=source/f'{side}_ankle_gimbal.step';old=cq.importers.importStep(str(path)).val()
 cutter=cq.Workplane('XY').box(8,34.9,2.4).val().translate((-42,sign*1.95,15.2))
 bridge=cq.Workplane('XY').box(8,34.9,2.4).val().translate((-42,sign*1.95,16.1))
 new=old.cut(cutter).fuse(bridge).clean()
 rows.append(dict(side=side,valid_single_solid=new.isValid() and len(new.Solids())==1,volume_change_mm3=new.Volume()-old.Volume(),source_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
 cq.exporters.export(new,str(a.out/f'{side}_ankle_gimbal.step'))
(a.out/'report.json').write_text(json.dumps({'rows':rows,'manufacturing_release':False},indent=2)+'\n');print(json.dumps(rows))
