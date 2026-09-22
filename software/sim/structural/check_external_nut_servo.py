"""Neutral assembly check against mapped manufacturer servo and ankle gimbal."""
from pathlib import Path
import argparse,json,hashlib
import cadquery as cq
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
step=Path('validation/x330_manufacturer_cad_v1/XL_XC_330.stp');mapping=Path('validation/x330_component_map_v1/report.json');meta=json.loads(mapping.read_text());assert hashlib.sha256(step.read_bytes()).hexdigest()==meta['source_sha256']
parts=cq.importers.importStep(str(step)).val().Solids();assert len(parts)==len(meta['components']);parts=[s.rotate((0,0,0),(-1,1,-1),120).translate((-3.5,0,0)) for s in parts]
plan={'scope':__doc__,'criteria':{'minimum_nominal_clearance_mm':1.1,'maximum_overlap_mm3':.01},'stop_condition':'One neutral assembly evaluation, both sides; no dimension sweep','limitations':['Tool cylinder is a reservation not a selected wrench','Neutral only; no motion clearance claim','Manufacturer CAD tolerance and mapping assumptions inherited','No harness or deflection']};(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');rows=[]
for side,cy in [('left',6),('right',-6)]:
 targets={str(i):s for i,s in enumerate(parts)};targets['gimbal']=cq.importers.importStep(f'validation/native_yoke_gimbal_wider_relief_v1/cad/{side}_ankle_gimbal.step').val().translate((26,0,10))
 shapes={n:cq.importers.importStep(f'validation/sole_external_nut_v1/{side}_{n}.step').val() for n in ['nut','screw']};shapes['tool_reservation']=cq.Solid.makeCylinder(4,20,cq.Vector(35,cy,-11.59))
 for name,shape in shapes.items():
  for index,fixed in targets.items():
   distance=shape.distance(fixed);volume=shape.intersect(fixed).Volume() if distance<1e-6 else 0
   rows.append({'side':side,'part':name,'target':index,'distance_mm':distance,'overlap_mm3':volume,'gate':distance>=1.1 and volume<=.01})
r={'rows':rows,'all_neutral_clearance_gates_pass':all(x['gate'] for x in rows),'manufacturing_release':False};(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'all_pass':r['all_neutral_clearance_gates_pass'],'minimum_distance_mm':min(x['distance_mm'] for x in rows),'failures':[x for x in rows if not x['gate']]},indent=2))
