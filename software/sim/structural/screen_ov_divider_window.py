"""Derive static divider feasibility without inventing source transient behavior."""
import argparse, itertools, json, hashlib
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
ref_min,ref_max,overdrive=.4925,.5075,.05
tol,leak,rlo=.001,10e-9,10000.
# At maximum permissible overdrive voltage, solve explicitly for upper resistor.
# This reserves zero transient allowance and is an optimistic bound, not a design target.
ceiling=6.
rhi_limit=(ceiling-(ref_max+overdrive))/((ref_max+overdrive)*(1+tol)/(rlo*(1-tol))+leak*(1+tol))
normal_upper=ref_min*(1+rhi_limit*(1-tol)/(rlo*(1+tol)))-leak*rhi_limit*(1-tol)
rows=[]
for rhi in [95300.,100000.]:
    corners=[]
    for hi,lo,ref,il in itertools.product([rhi*(1-tol),rhi*(1+tol)],[rlo*(1-tol),rlo*(1+tol)],[ref_min,ref_max],[-leak,leak]):
        corners.append([ref*(1+hi/lo)+il*hi,(ref+overdrive)*(1+hi/lo)+il*hi])
    trip_min=min(c[0] for c in corners);over_max=max(c[1] for c in corners)
    rows.append({'Rhigh_ohm':rhi,'Rlow_ohm':rlo,'minimum_trip_V':trip_min,
                 'maximum_trip_V':max(c[0] for c in corners),
                 'maximum_voltage_for_50mV_overdrive_V':over_max,
                 'margin_from_5V_to_min_trip_V':trip_min-5,
                 'remaining_voltage_to_6V_after_overdrive_V':ceiling-over_max})
r={'comparison_only':True,'resistor_tolerance_assumption':tol,
   'source':'validation/servo_ov_threshold_v1/report.json',
   'source_sha256':hashlib.sha256(Path('validation/servo_ov_threshold_v1/report.json').read_bytes()).hexdigest(),
   'optimistic_Rhigh_upper_bound_ohm':rhi_limit,
   'normal_voltage_ceiling_for_nonempty_window_V':normal_upper,
   'rows':rows,'qualified':False,
   'decision':'95.3k/10k narrows normal-rail margin while providing positive static overdrive headroom. Do not adopt until normal UBEC envelope and actual 5V fault timing are bounded.',
   'limits':['No allowance for output rise during propagation and FET turnoff',
             '50mV delay specification is at 12V, not a timing guarantee at 5V',
             'Leakage specification test point and resistor lifetime drift limitations retained',
             'Normal voltage must be strictly below minimum trip; equality is not acceptable']}
(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
