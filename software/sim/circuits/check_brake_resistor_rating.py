"""Conditional rating comparison; preserve distinction from actual thermal qualification."""
import json,hashlib
from pathlib import Path
p=Path('validation/brake_resistor_rating_review_v1');plan=json.loads((p/'plan.json').read_text())
paths=[Path(x) for x in plan['sources']];c,r=[json.loads(f.read_text()) for f in paths]
burden=r['post_disconnect_absorber_measurements'];limit=plan['criteria']['each_peak_W_max']
checks={f'branch{i}_peak_below_conditional_rating':burden[f'brake{i}_peak_W']<=limit for i in [0,1]}
rmin=c['resistance_ohm']*(1-c['tolerance_fraction']);bound=6**2/rmin
result={'checks':checks,'conditional_P70_W':limit,'measured_primary_peak_W':burden['brake0_peak_W'],'measured_primary_energy_J':burden['brake0_energy_J'],'six_V_tolerance_only_power_bound_W':bound,'six_V_tolerance_only_bound_below_rating':bound<=limit,'two_resistor_mass_g':2*c['mass_each_g'],'thermal_design_verified':False,'source_sha256':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in paths}}
(p/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
