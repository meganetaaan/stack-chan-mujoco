"""Extract mass-input coefficients, without treating collision envelopes as hardware mass."""
import argparse,csv,hashlib,json
from pathlib import Path
from collections import defaultdict
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
root=Path(__file__).resolve().parents[3];src=root/'board/mechanical/prototype/yaw_support_candidate/revA/inventory.json';d=json.loads(src.read_text())
groups=defaultdict(list)
for part in d['parts']:
 n=part['name']
 if n in ('body_shroud','rear_plate'):key=n
 elif n.endswith('yaw_fixed_support'):key='yaw_fixed_support'
 elif n.endswith('threaded_backing_plate'):key='threaded_backing_plate'
 elif n.endswith('mount_plate'):key='mount_plate'
 elif n.endswith('rear_washer'):key='rear_washer'
 elif '_plate_' in n and n.endswith('_washer'):key='mount_washer'
 else:key='hardware_envelopes'
 groups[key].append(part)
rows=[]
for key,parts in groups.items():
 v=sum(x['volume_mm3'] for x in parts)/1000
 rows.append({'group':key,'quantity':len(parts),'CAD_volume_cm3':v,'mass_g_per_density_g_cm3':v if key!='hardware_envelopes' else '', 'mass_method':'part manufacturer mass or real thread geometry required' if key=='hardware_envelopes' else 'nominal solid volume times declared effective density; process verification pending','density_g_cm3':'','qualified_mass_g':''})
assert sum(r['quantity'] for r in rows)==52
with (a.out/'mass_inputs.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
report={'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'parts_accounted':52,'nominal_volume_coefficients_only':True,'robot_mass_updated':False,'frozen_model_mass_must_not_be_incremented_blindly':True,'exclusions':['Servos/horns/case screws','Body corner fasteners','Legs/feet','Tab5/battery/electronics/wiring'],'required_before_load_update':['Manufacturing process and effective density','Hardware actual mass','Mapping replacing existing model components, not double counting','Mass centres and inertia tensors in assembled frame']}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(rows,indent=2))
