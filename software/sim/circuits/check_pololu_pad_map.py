"""Validate a manually reviewed manufacturer pad mapping against drill/placement data."""
import argparse,csv,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
files={'map':'schematics/power/dual_pololu_pad_map.json','drill':'validation/dual_pololu_drill_v1/report.json','placement':'validation/dual_pololu_mounted_layout_v1/report.json','interface':'schematics/power/dual_pololu_interface.json'}
d={k:json.loads(Path(v).read_text()) for k,v in files.items()}
pads=d['map']['pads'];xy=[tuple(x['local_xy_mm']) for x in pads]
assert len(pads)==18 and len(set(xy))==18
mounts={tuple(x) for x in d['drill']['mount_centers_mm']};unknown={tuple(x['local_xy_mm']) for x in d['map']['unassigned_crosshairs']}
assert not (set(xy)&mounts or set(xy)&unknown or mounts&unknown)
assert set(xy)|mounts|unknown=={tuple(x['center_local_mm']) for x in d['drill']['all_crosshairs']}
assert set(x['signal'] for x in pads)==set(d['interface']['ports_each'])
selected=sorted((x for x in pads if x['selected_power_connection']),key=lambda x:x['local_xy_mm'][0])
assert [x['signal'] for x in selected]==['VIN','GND','GND','VOUT']
rows=[]
for placement in d['placement']['placements']:
 side=placement['side'].upper();tx,ty,tz=placement['step_translation_mm']
 for pad in selected:
  cfg=d['interface']['ports_each'][pad['signal']];net=cfg['net_pattern'].format(SIDE=side) if 'net_pattern' in cfg else cfg['net']
  x,y=pad['local_xy_mm'];rows.append({'module':side+'_U_REGULATOR','pad_project_id':pad['id'],'signal':pad['signal'],'net':net,'local_x_mm':x,'local_y_mm':y,'robot_x_mm':round(tx+x,5),'robot_y_mm':round(ty+y,5),'robot_pcb_underside_z_mm':tz})
assert len(rows)==8
assert {r['net'] for r in rows if r['signal']=='VOUT'}=={'LEFT_REGULATOR_OUT','RIGHT_REGULATOR_OUT'}
report={'status':'document_mapping_checked_not_manufacturing_release','source_sha256':{k:hashlib.sha256(Path(v).read_bytes()).hexdigest() for k,v in files.items()},'mapped_electrical_holes':18,'mounting_holes':4,'unassigned_crosshairs':1,'selected_power_connections':8,'coverage_of_drill_crosshairs':23,'checks':{'unique_pad_positions':True,'drill_coverage_complete':True,'functional_signals_match_interface':True,'selected_power_order_matches_reviewed_images':True,'independent_output_nets':True},'manual_review_required':'Source photographs establish signal identity and orientation; script only checks the recorded mapping and transforms.','hardware_verified':False,'manufacturing_release':False}
a.out.mkdir(parents=True,exist_ok=True)
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
with (a.out/'power_connections.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
print(json.dumps(report,indent=2))
