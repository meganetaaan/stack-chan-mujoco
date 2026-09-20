"""Open the lower bridge center to clear the native idler-mounted yoke."""
import argparse,hashlib,json
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[3]
if a.out.exists():p.error('new output required')
a.out.mkdir(parents=True)
source=root/'validation/gimbal_real_case_relief_development_v1/cad'
plan=dict(scope=__doc__,cut_x_mm=[-55.4,-53],cut_z_mm=[-18.8,-16.4],cut_y_relative_to_center_mm=[-16.05,16.05],
          criteria={'valid_single_solid':True,'neutral_yoke_overlap_max_mm3':.01},
          limitations=['Removal changes stiffness and load path; strength must be recomputed','No whole-robot clearance or screw qualification'])
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');rows=[]
for side,sign in [('left',1),('right',-1)]:
 path=source/f'{side}_ankle_gimbal.step';old=cq.importers.importStep(str(path)).val()
 cut=cq.Workplane('XY').box(2.4002,32.1,2.4002).val().translate((-54.2,sign*1.95,-17.6))
 new=old.cut(cut).clean()
 yoke=cq.importers.importStep(str(root/f'validation/native_horn_yoke_development_v1/v4/{side}_foot_yoke.step')).val()
 before=old.translate((26,0,10));after=new.translate((26,0,10))
 row=dict(side=side,valid_single_solid=new.isValid() and len(new.Solids())==1,removed_volume_mm3=old.Volume()-new.Volume(),
          original_yoke_overlap_mm3=before.intersect(yoke).Volume(),candidate_yoke_overlap_mm3=after.intersect(yoke).Volume(),candidate_yoke_distance_mm=after.distance(yoke),source_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
 rows.append(row);cq.exporters.export(new,str(a.out/f'{side}_ankle_gimbal.step'))
(a.out/'report.json').write_text(json.dumps({'rows':rows,'structural_verified':False},indent=2)+'\n');print(json.dumps(rows,indent=2))
