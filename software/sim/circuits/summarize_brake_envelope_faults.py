"""Compare recorded open-fault simulations against predeclared voltage/rating screens."""
import json,hashlib
from pathlib import Path
p=Path('validation/brake_51ohm_envelope_faults_v1');plan=json.loads((p/'plan.json').read_text());cases={};hashes={}
for fault in plan['faults']:
 f=p/fault/'report.json';r=json.loads(f.read_text());peak=r['bus_after_disconnect_max_V'];hashes[str(f)]=hashlib.sha256(f.read_bytes()).hexdigest()
 cases[fault]={'bus_max_V':peak,'voltage_screen_pass':peak<=plan['criteria']['post_disconnect_bus_max_V'],'absorber_measurements':r['post_disconnect_absorber_measurements']}
bound=plan['criteria']['post_disconnect_bus_max_V']**2/plan['Rmin_ohm']
result={'cases':cases,'six_V_Rmin_power_bound_W':bound,'conditional_rating_screen_pass':bound<=plan['criteria']['conditional_P70_W'],'design_verified':False,'source_sha256':hashes}
(p/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
