"""Single fixed cell-envelope placement against current yaw CAD; no holder or pack fit claim."""
import argparse,hashlib,json
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--spec',type=Path,default=Path('validation/direct_cell_p30b_v1/cell_candidate.json'));a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
cp=a.spec;spec=json.loads(cp.read_text());root=Path('validation/yaw_integrated_candidate_v4');ip=root/'inventory.json';sp=root/'yaw_support_candidate.step'
place=Path('validation/rc_battery_cad_v1_checked/report.json');centre=json.loads(place.read_text())['center_base_mm'];d=spec['dimensions_max_mm'];radius=d['diameter']/2;length=d['height']
plan={'cell':str(cp),'placement':'Reuse old battery centre, cylinder axis +Y. No position search.','centre_base_mm':centre,'source_sha256':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in [cp,ip,sp,place]},'stop':'One cylinder at manufacturer max dimensions vs 52 fixed parts and retained Tab5; no tray redesign or release.','limits':['Bare cell only, no insulation/holder/end contacts/leads/protection','No dynamic clearance or extraction','Nominal geometry; no printing/deformation allocation']}
if 'package_limits' in spec: plan['limits']=spec['package_limits']
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
cell=cq.Solid.makeCylinder(radius,length,cq.Vector(centre[0],centre[1]-length/2,centre[2]),cq.Vector(0,1,0));cq.exporters.export(cell,str(a.out/'cell_envelope.step'))
parts=json.loads(ip.read_text())['parts'];solids=cq.importers.importStep(str(sp)).val().Solids();assert len(parts)==len(solids)==52;rows=[]
for part,solid in zip(parts,solids):
 assert abs(part['volume_mm3']-solid.Volume())<1e-5
 rows.append({'part':part['name'],'overlap_mm3':cell.intersect(solid).Volume(),'distance_mm':cell.distance(solid)})
tabpath=Path('software/sim/mujoco/assets/r9_fast_turn_v1/cad/Tab5.step');tab=cq.importers.importStep(str(tabpath)).val();rows.append({'part':'Tab5','overlap_mm3':cell.intersect(tab).Volume(),'distance_mm':cell.distance(tab)})
report={'rows':rows,'tab5_source_sha256':hashlib.sha256(tabpath.read_bytes()).hexdigest(),'overlapping_parts':[r['part'] for r in rows if r['overlap_mm3']>1e-6],'minimum_nominal_distance_mm':min(r['distance_mm'] for r in rows),'cell_only_mass_max_g':spec.get('mass_max_g'),'listed_mass_g':spec.get('mass_g',spec.get('mass_max_g')),'mass_classification':spec.get('mass_classification','manufacturer maximum bare-cell mass'),'pack_and_holder_fit_verified':False,'manufacturing_release':False}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='rows'},indent=2))
