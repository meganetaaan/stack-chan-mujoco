"""Replace legacy battery/converter/tray origin moments with selected-layout candidates."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
import cadquery as cq
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--base',type=Path,default=Path('validation/yaw_inertial_ledger_v2/report.json'));a=p.parse_args()
base=a.base;r=json.loads(base.read_text())
supply=Path('schematics/power/rc_supply_candidate.json');s=json.loads(supply.read_text())
material=Path('board/mechanical/prototype/rc_battery_tray_revB/material_candidate.json');mat=json.loads(material.read_text())
layout=Path('board/mechanical/prototype/power_packaging_revA/report.json');layout_data=json.loads(layout.read_text())
entries=[('battery','validation/rc_battery_cad_v1_checked/battery_candidate.step',s['battery']['catalog_mass_g']/1000),
 ('UBEC_left','validation/dual_ubec_layout_v2/left.step',s['regulator']['mass_g']/1000),
 ('UBEC_right','validation/dual_ubec_layout_v2/right.step',s['regulator']['mass_g']/1000),
 ('tray','board/mechanical/prototype/rc_battery_tray_revB/tray.step',None)]
added={};details=[];sources=[base,supply,material,layout]
for name,filename,mass in entries:
 path=Path(filename);sha=hashlib.sha256(path.read_bytes()).hexdigest();assert layout_data['sources_sha256'][filename]==sha
 shape=cq.importers.importStep(filename).val();assert shape.isValid()
 volume=shape.Volume();com=np.array(shape.Center().toTuple())*.001
 if mass is None:mass=volume*mat['typical_density_g_cm3']*1e-6
 I=np.array(cq.Shape.matrixOfInertia(shape))*mass/volume*1e-6
 added[name]={'mass_kg':mass,'first_moment_kg_m':(mass*com).tolist(),'inertia_origin_kg_m2':(I+mass*(com@com*np.eye(3)-np.outer(com,com))).tolist()}
 details.append({'name':name,'mass_kg':mass,'com_m':com.tolist(),'inertia_com_kg_m2':I.tolist(),'distribution':'uniform CAD solid scaled to catalog mass' if name!='tray' else 'uniform PETG solid at typical candidate density'})
 sources.append(path)
removed={name:r['retained_old_allocations'][name] for name in ['battery_2S_reservation','dedicated_5V_converter','battery_tray']}
new={};delta={}
for key,value in r['fixed_terms_including_retained_reservations'].items():
 d=sum((np.asarray(v[key]) for v in added.values()),np.zeros_like(np.asarray(value)))-sum((np.asarray(v[key]) for v in removed.values()),np.zeros_like(np.asarray(value)))
 delta[key]=d.tolist();new[key]=(np.asarray(value)+d).tolist()
retained={k:v for k,v in r['retained_old_allocations'].items() if k not in removed}
# Independent reconstruction from itemized retained, metal, washers and new payload.
for key in new:
 total=sum((np.asarray(v[key]) for group in [retained,r['new_metal_parts'],r['selected_SUS304_mount_washers'],added] for v in group.values()),np.zeros_like(np.asarray(new[key])))
 assert np.allclose(total,new[key],rtol=0,atol=1e-14)
m=new['mass_kg'];c=np.array(new['first_moment_kg_m'])/m
I=np.array(new['inertia_origin_kg_m2'])-m*(c@c*np.eye(3)-np.outer(c,c))
assert min(np.linalg.eigvalsh(I))>0
report={'sources_sha256':{str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in sources},'frame':'base CAD coordinates; inherited yaw ledger frame',
 'removed_old_allocations':removed,'added_candidate_allocations':added,'added_part_details':details,'delta_origin_terms':delta,
 'retained_old_allocations':retained,'new_metal_parts':r['new_metal_parts'],'selected_SUS304_mount_washers':r['selected_SUS304_mount_washers'],'homogeneous_density_coefficients_per_kg_m3':r['homogeneous_density_coefficients_per_kg_m3'],'updated_fixed_terms':new,'fixed_subtotal_com_m':c.tolist(),'fixed_subtotal_inertia_com_kg_m2':I.tolist(),
 'itemized_reconstruction_pass':True,'whole_base_complete':False,'model_updated':False,'manufacturing_release':False,
 'remaining':[x for x in r['unresolved'] if not x.startswith(('Retained battery/electronics/tray reservations','Old battery/electronics/tray reservations retained explicitly'))]+['Internal battery and converter mass distribution is not known; uniform solid is a comparison.', 'TTL, strap, all wiring and protection PCB/components still require allocation.', 'These are selected packaging candidates, not electrically qualified supplies.']}
a.out.mkdir(parents=True,exist_ok=False);(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'payload_mass_delta_kg':delta['mass_kg'],'new_fixed_subtotal_kg':m,'first_moment_delta_kg_m':delta['first_moment_kg_m']}))
