"""Evaluate a saved conditional resistance envelope without replacing earlier nominal screens."""
import json
from pathlib import Path
p=Path('validation/brake_resistor_envelope_v1');a=json.loads((p/'plan.json').read_text())
r=a['nominal_ohm'];dt=a['wire_temperature_C_assumed']-a['reference_temperature_C_assumed'];tf=1+a['TCR_per_K_min']*dt
cases={'initial_only':r*(1-a['initial_tolerance_fraction']), 'initial_and_temperature':r*(1-a['initial_tolerance_fraction'])*tf,
       'initial_endurance_and_temperature':(r*(1-a['initial_tolerance_fraction']-a['endurance_change_fraction'])-a['endurance_change_absolute_ohm'])*tf}
assert all(v>0 for v in cases.values())
limit=a['criteria']['conditional_P70_W'];v=a['bus_bound_V']
result={'cases':{k:{'resistance_min_ohm':x,'power_at_bus_bound_W':v*v/x,'below_conditional_rating':v*v/x<=limit} for k,x in cases.items()},
        'required_nominal_ohm_for_combined_envelope':(v*v/limit/tf+a['endurance_change_absolute_ohm'])/(1-a['initial_tolerance_fraction']-a['endurance_change_fraction']),
        'thermal_design_verified':False}
(p/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
