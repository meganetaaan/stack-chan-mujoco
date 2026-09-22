"""Single nominal mounting hypothesis for OEM side frames at yaw servos."""
import argparse,json,hashlib
from pathlib import Path
import cadquery as cq
ROOT=Path(__file__).resolve().parents[3];p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
plan={'question':'Can OEM side frames replace direct shelf screws without support changes?', 'mapping':'Frame X along robot X, 23 mm inner width spans case Z=65..88, inner side face at Y=cy+/-10. Four ear axes map to case X=-27.5/2.5 and Y=cy+/-8.', 'mapping_status':'Dimension/axis-derived mounting hypothesis, not verified assembly instruction', 'stop':'One orientation per side face; record collisions, no optimization sweep.', 'intersection_limit_mm3':.01,'limitations':['No screws or tool sweeps','No manufacturer load rating','No preload or strength','Frame mounting to body still requires design']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');src=ROOT/'validation/yaw_oem_frame_review_v1/fpx330-s101.stp';frame=cq.importers.importStep(str(src)).val();servo=cq.importers.importStep(str(ROOT/'validation/x330_manufacturer_cad_v1/XL_XC_330.stp')).val().Solids();rows=[]
for side,cy in [('left',26),('right',-26)]:
 support=cq.importers.importStep(str(ROOT/f'validation/yaw_case_mount_v2/{side}_yaw_fixed_support.step')).val()
 case=cq.Compound.makeCompound([s.rotate((0,0,0),(1,1,0),180).translate((-5,cy,68.5)) for i,s in enumerate(servo) if i not in [10,11,12]])
 for sign in [-1,1]:
  f=frame if sign==1 else frame.rotate((0,0,0),(1,0,0),180)
  f=f.translate((-12.5,cy+sign*10,76.5));cq.exporters.export(f,str(a.out/f'{side}_{sign}_frame.step'))
  for name,s in [('support',support),('servo',case)]:
   v=float(f.intersect(s).Volume());rows.append({'side':side,'face_sign':sign,'target':name,'overlap_mm3':v,'pass':v<=.01})
r={'rows':rows,'manufacturer_frame_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'manufacturing_release':False,'limitations':plan['limitations']};(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(rows,indent=2))
