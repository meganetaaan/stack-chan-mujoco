"""Nominal static battery-box interference against current yaw CAD and retained payloads."""
import argparse,hashlib,json
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
invpath=Path('board/mechanical/prototype/yaw_support_candidate/revA/inventory.json');inv=json.loads(invpath.read_text())
placementpath=Path('validation/rc_battery_envelope_v1/report.json');placement=json.loads(placementpath.read_text());dims=placement['minimum_total_extension_orientation']['oriented_size_mm'];center=placement['old_center_base_mm']
battery=cq.Workplane('XY').box(*dims).val().translate(tuple(center))
sources={x['name']:(Path(x['source']),x.get('source_sha256')) for x in inv['parts'] if x['source']}
sources['complete_yaw_assembly']=(invpath.parent/'yaw_support_candidate.step',None)
base=Path('software/sim/mujoco/assets/r9_fast_turn_v1/cad')
for name in ('Tab5','battery_tray','battery_strap_envelope','dedicated_5V_converter','TTL_interface','left_battery_screw_envelope','right_battery_screw_envelope','left_yaw_motor_case','right_yaw_motor_case'):
 if name not in sources:sources[name]=(base/(name+'.step'),None)
rows=[]
for name,(path,expected) in sources.items():
 digest=hashlib.sha256(path.read_bytes()).hexdigest()
 if expected and digest!=expected:raise ValueError('Stale source: '+name)
 shape=cq.importers.importStep(str(path)).val()
 if not shape.isValid():raise ValueError(name)
 overlap=battery.intersect(shape).Volume();distance=battery.distance(shape)
 rows.append({'part':name,'source':str(path),'sha256':digest,'overlap_mm3':overlap,'distance_mm':distance})
cq.exporters.export(battery,str(a.out/'battery_candidate.step'))
r={'scope':'Nominal static base-frame box; current yaw assembly plus retained r9 payload geometry','placement_sha256':hashlib.sha256(placementpath.read_bytes()).hexdigest(),'inventory_sha256':hashlib.sha256(invpath.read_bytes()).hexdigest(),'dimensions_mm':dims,'center_base_mm':center,'rows':rows,'overlapping_parts':[x['part'] for x in rows if x['overlap_mm3']>1e-6],'numerical_overlap_reporting_threshold_mm3':1e-6,'manufacturing_release':False,'limitations':['Reservation box omits leads, swelling, tolerances and padding','Retained converter and interface are old candidates','No extraction or motion path checked','No new tray or retention designed']}
(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'parts_checked':len(rows),'overlaps':[(x['part'],x['overlap_mm3']) for x in rows if x['overlap_mm3']>1e-6]}))
