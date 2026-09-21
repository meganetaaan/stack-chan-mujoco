"""Conditional source-disconnected discharge envelope, including sustained backfeed."""
import argparse,json,math
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
# Design choices fixed before calculation: 100k bleed, 3.5V target, no time requirement.
rmax=100000*1.01;rmin=100000*.99;v0=12.6;target=3.5
c_local=json.loads(Path('validation/logic_branch_bypass_v1/report.json').read_text())['rows'][0]['C_25_to_125C_F'][1]
rows=[]
for backfeed in [0,10e-6,40e-6]:
 eq=backfeed*rmax
 factor=math.log((v0-eq)/(target-eq)) if eq<target else None
 rows.append({'backfeed_A':backfeed,'equilibrium_V':eq,'can_reach_target':eq<target,'seconds_per_uF':None if factor is None else rmax*1e-6*factor,'local_caps_only_time_s':None if factor is None else rmax*c_local*factor})
d={'engineering_choices':{'bleed_ohm':100000,'total_resistor_tolerance':.01,'start_V':v0,'target_V':target,'required_reset_time_s':None},'manufacturer_derived_POR_fall_lower_V':3.9-.3,'maximum_sustained_backfeed_for_target_A_exclusive':target/rmax,'battery_current_at_12p6V_upper_A':v0/rmin,'resistor_power_at_12p6V_upper_W':v0*v0/rmin,'cases':rows,'whole_system_capacitance_F':None,'qualified':False,'limits':['Capacitance on shared BATTERY_RAW includes unmodelled converter inputs; local time is not robot reset time','Backfeed cases are diagnostic assumptions, not measured bounds','Other passive/IC discharge paths omitted; no helpful minimum load assumed','POR voltage crossing alone does not establish reset pulse duration or safe servo rearm']}
(a.out/'report.json').write_text(json.dumps(d,indent=2)+'\n');assert d['manufacturer_derived_POR_fall_lower_V']>target;assert rows[0]['can_reach_target'] and not rows[2]['can_reach_target'];print(json.dumps(d,indent=2))
