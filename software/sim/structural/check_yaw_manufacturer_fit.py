"""Check manufacturer X330 geometry at the frozen yaw output axes before insertion analysis."""
import argparse,json,hashlib
from pathlib import Path
import cadquery as cq
ROOT=Path(__file__).resolve().parents[3]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
plan={'question':'Does actual servo CAD fit the support in its final pose, prerequisite to insertion-path work?',
      'mapping':'Rotate manufacturer CAD 180 degrees about (1,1,0): (x,y,z)->(y,x,-z); translate to (-5,+/-26,68.5) mm. Front horn face z=6.5 maps to robot z=62.',
      'mapping_status':'Design orientation hypothesis; validate bounding envelope against frozen case; not physical calibration.',
      'stop':'One final pose per side; do not run insertion sweeps if final fit fails.',
      'intersection_limit_mm3':.01,'criterion_source':'Existing geometric screening assumption; not contact strength.',
      'limitations':['no screw interfaces or wiring','manufacturer nominal CAD','no insertion-path proof','no support strength']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
sources={}
def read(p):
 sources[str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest();return cq.importers.importStep(str(p)).val()
raw=read(ROOT/'validation/x330_manufacturer_cad_v1/XL_XC_330.stp').Solids()
meta=json.loads((ROOT/'validation/x330_component_map_v1/report.json').read_text())
assert len(raw)==len(meta['components'])
rows=[];bounds=[]
for side,y in [('left',26),('right',-26)]:
 support=read(ROOT/f'validation/inset_yaw_assembly_development_v1/yaw_inset_mount_v1/{side}_yaw_fixed_support.step')
 reserved=read(ROOT/f'software/sim/mujoco/assets/r9_fast_turn_v1/cad/{side}_yaw_motor_case.step')
 rb=reserved.BoundingBox()
 for i,s in enumerate(raw):
  mapped=s.rotate((0,0,0),(1,1,0),180).translate((-5,y,68.5))
  d=float(mapped.distance(support));v=float(mapped.intersect(support).Volume()) if d<1e-6 else 0.
  rows.append({'side':side,'component':i,'name':meta['components'][i]['product_name'],'distance_mm':d,'overlap_mm3':v,'pass':v<=.01})
  if i in [0,1,2]:
   b=mapped.BoundingBox();bounds.append({'side':side,'component':i,'bounds':[b.xmin,b.xmax,b.ymin,b.ymax,b.zmin,b.zmax],'reserved_case_bounds':[rb.xmin,rb.xmax,rb.ymin,rb.ymax,rb.zmin,rb.zmax]})
r={'rows':rows,'case_bounds':bounds,'source_sha256':sources,'final_pose_intersections_pass':all(x['pass'] for x in rows),'manufacturing_release':False,'limitations':plan['limitations']}
(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'failures':[x for x in rows if not x['pass']],'case_bounds':bounds},indent=2))
