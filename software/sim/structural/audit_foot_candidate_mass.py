"""Nominal solid-volume mass estimate; not a measured or released robot mass."""
from pathlib import Path
import json,hashlib
p=Path('validation/foot_candidate_mass_v1');inventory=Path('board/mechanical/prototype/foot_candidate/revA/inventory.json');data=json.loads(inventory.read_text())
plan={'density_assumptions_kg_m3':{'boot':1270,'yoke':1270,'sole':1200,'spacer':8000,'nut':8000},'purchased_screw_mass_each_g':.23,'previous_screw_mass_each_g':.19,'scope':'Six-component feet only, solid CAD volumes; not an infill prediction','limitations':['Densities are engineering assumptions, not qualified printed material cards','Nut is an unthreaded envelope estimate','Screw uses manufacturer nominal mass instead of solid cylindrical envelope','No servo horn bolts harness or adhesive included','No new dynamics run or old load qualification']};(p/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
rows=[]
for row in data['parts']:
 density=plan['density_assumptions_kg_m3'].get(row['part']);mass=.23 if row['part']=='screw' else row['volume_mm3']*density*1e-6
 rows.append({'side':row['side'],'part':row['part'],'mass_g':mass,'basis':'manufacturer nominal' if density is None else 'assumed solid density','density_kg_m3':density})
delta_source=Path('validation/sole_external_nut_v1/report.json');delta_rows=json.loads(delta_source.read_text())['rows']
result={'parts':rows,'mass_each_foot_g':{side:sum(x['mass_g'] for x in rows if x['side']==side) for side in ['left','right']},'delta_external_vs_captive_nut_design_g_per_foot':{r['side']:r['added_yoke_volume_mm3']*1270e-6+.23-.19 for r in delta_rows},'delta_note':'Filled yoke pocket plus 8-to-10mm screw only; nut moved but same part; not difference from frozen MuJoCo foot','source_sha256':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in [inventory,delta_source]},'whole_robot_mass_kg':None,'old_dynamic_loads_validated_for_candidate':False};(p/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='parts'},indent=2))
