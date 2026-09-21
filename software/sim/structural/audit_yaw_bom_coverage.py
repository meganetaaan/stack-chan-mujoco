"""Reconcile every yaw candidate solid to a BOM line, separating shared foot quantities."""
import argparse,csv,hashlib,json,re
from pathlib import Path
root=Path(__file__).resolve().parents[3]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
paths=['board/mechanical/prototype/yaw_support_candidate/revA/inventory.json','docs/prototype/engineering/prototype_decision/candidate_bom.csv']
parts=json.loads((root/paths[0]).read_text())['parts'];bom={r['item']:r for r in csv.DictReader((root/paths[1]).open())}
rules=[('body_shroud','Yaw candidate body shroud',0),('rear_plate','A5052P-H34 rear structural plate t2 mm',0),('(left|right)_yaw_fixed_support','Yaw fixed support keeper-v2',0),('(left|right)_threaded_backing_plate','A5052P-H34 threaded backing plate t3 mm',0),('(left|right)_mount_plate','SUS304 yaw servo mount plate t1 mm',0),('(left|right)_(rear_[0-3]_bolt)','NBK SNS-M3-16 yaw rear main bolts',0),('(left|right)_rear_[0-3]_rear_washer','Yaw rear M3 washer OD7 ID3.2 t0.5 mm',0),('(left|right)_(plate_[0-3]_screw|64_keeper|76_keeper)','NBK SLH-M2-10 screw',2),('(left|right)_plate_[0-3]_washer','SCW-SOLE-SPACER-01 revA',2),('(left|right)_plate_[0-3]_nut','PTS A56202 external nut',2)]
coverage=[];seen=[]
for pattern,item,feet in rules:
 names=[v['name'] for v in parts if re.fullmatch(pattern,v['name'])];assert names,item
 assert item in bom,item
 quantity=int(bom[item]['quantity_full_robot']);assert quantity==len(names)+feet,(item,quantity,len(names),feet)
 coverage.append({'item':item,'yaw_quantity':len(names),'foot_quantity':feet,'BOM_quantity':quantity,'yaw_parts':names,'status':bom[item]['status']});seen+=names
assert len(seen)==len(set(seen))==len(parts)==52
report={'source_sha256':{x:hashlib.sha256((root/x).read_bytes()).hexdigest() for x in paths},'coverage':coverage,'yaw_parts_mapped_exactly_once':52,'bom_family_count':len(coverage),'quantity_check_passed':True,'scope':'Only 52-solid yaw candidate and explicit shared foot quantities; not complete robot procurement','excluded_from_assembly':['Servos horns and case tapping screws','Body corner fasteners','Legs and other foot parts','Electronics wires connectors','Tools spares and test coupons'],'manufacturing_release':False}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['yaw_parts_mapped_exactly_once','bom_family_count','quantity_check_passed','manufacturing_release']}))
