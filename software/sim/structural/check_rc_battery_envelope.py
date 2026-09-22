"""Compare candidate battery orientations with the old reservation, not the cavity."""
import argparse,hashlib,itertools,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
robotpath=Path('board/mechanical/prototype/robot.json');packpath=Path('schematics/power/rc_supply_candidate.json')
robot=json.loads(robotpath.read_text());pack=json.loads(packpath.read_text())['battery'];old=robot['battery_envelope'];rows=[]
for dims in sorted(set(itertools.permutations(pack['catalog_dimensions_mm']))):
 excess=[max(0,x-y) for x,y in zip(dims,old['size_mm'])]
 rows.append({'oriented_size_mm':dims,'exceeds_reservation_by_axis_mm':excess,'inside_old_reservation':not any(excess)})
choice=min(rows,key=lambda x:sum(x['exceeds_reservation_by_axis_mm']))
center=old['center_base_mm'];dims=choice['oriented_size_mm']
result={'sources_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (robotpath,packpath)},'old_reservation_size_mm':old['size_mm'],'old_center_base_mm':center,'orientations':rows,'minimum_total_extension_orientation':choice,'candidate_bounds_at_old_center_mm':[[c-d/2,c+d/2] for c,d in zip(center,dims)],'candidate_nominal_mass_kg':pack['catalog_mass_g']/1000,'old_reservation_mass_kg':old['mass_kg'],'nominal_mass_delta_kg':pack['catalog_mass_g']/1000-old['mass_kg'],'cavity_fit_verified':False,'manufacturing_release':False,'decision':'Old reservation is too thin for every axis-aligned orientation; check actual tray/cavity and replacement retention before adoption','excluded':['Leads and connectors','Pack dimensional tolerance and swelling allowance','Padding and strap clearance','Actual body/tray collisions and extraction path']}
(a.out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(choice));print(result['candidate_bounds_at_old_center_mm'])
