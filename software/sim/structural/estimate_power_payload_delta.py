"""Partial mass/first-moment replacement estimate; no whole-body inertia release."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
import cadquery as cq
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
paths=[Path('validation/yaw_inertial_ledger_v2/report.json'),Path('schematics/power/rc_supply_candidate.json'),Path('board/mechanical/prototype/rc_battery_tray_revB/material_candidate.json'),Path('board/mechanical/prototype/rc_battery_tray_revB/tray.step'),Path('validation/dual_ubec_layout_v2/report.json')]
old=json.loads(paths[0].read_text())['retained_old_allocations'];parts=json.loads(paths[1].read_text());material=json.loads(paths[2].read_text());layout=json.loads(paths[4].read_text());tray=cq.importers.importStep(str(paths[3])).val()
removed={k:old[k] for k in ['battery_2S_reservation','dedicated_5V_converter','battery_tray']}
added=[{'name':'battery','mass_kg':parts['battery']['catalog_mass_g']/1000,'com_m':[.029,0,.080],'basis':'catalog mass; COM assumed geometric center'},{'name':'tray_revB','mass_kg':material['solid_density_mass_estimate_g']/1000,'com_m':(np.array(tray.Center().toTuple())/1000).tolist(),'basis':'uniform solid at typical PETG density, not printed mass'}]
for side,c in zip(['left','right'],layout['centers_mm']):added.append({'name':'UBEC_'+side,'mass_kg':parts['regulator']['mass_g']/1000,'com_m':(np.array(c)/1000).tolist(),'basis':'catalog mass; entire mass assigned to case center; wire mass distribution unknown'})
om=sum(x['mass_kg'] for x in removed.values());nm=sum(x['mass_kg'] for x in added);of=sum((np.array(x['first_moment_kg_m']) for x in removed.values()),np.zeros(3));nf=sum((x['mass_kg']*np.array(x['com_m']) for x in added),np.zeros(3))
r={'scope':'partial replacement estimate, not new robot mass or COM','removed':removed,'added':added,'delta_mass_kg':nm-om,'delta_first_moment_kg_m':(nf-of).tolist(),'sources_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},'excluded':['New wiring mounts protection and real strap','TTL replacement','Actual battery/UBEC COM and inertia','Printed voids and process variation'],'model_updated':False};(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(r['delta_mass_kg'],r['delta_first_moment_kg_m'])
