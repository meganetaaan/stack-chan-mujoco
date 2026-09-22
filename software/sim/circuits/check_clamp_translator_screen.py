"""Screen a dual-supply replacement against the existing U10 MR interface."""
import json
from pathlib import Path
from argparse import ArgumentParser
p=ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
vmin,vmax=4.75,5.25
mr_pullup_min=70000
ioff=2.5e-6
# Conservative independent voltage extrema; no interpolated high-drive guarantee.
low_current=vmax/mr_pullup_min+ioff
r_off_max=.3*vmin/low_current
# Sufficient condition for use of the rail-wide 100 uA VOH row.
r_high_min=vmax/100e-6
report={'candidate':'TXU0101 (DBV 6-pin)','direct_replacement_accepted':False,'reason':'Output isolation is high impedance; U10 MR has an internal pullup. Loss of VCCA does not force clamp assertion.', 'assumptions':{'VCCB_V':[vmin,vmax],'existing_required_default':'U10 MR Low with LOGIC3V3 absent','resistor_tolerance_fraction':.01},'manufacturer_conditions':{'MR_pullup_min_ohm':mr_pullup_min,'MR_VIL_fraction':.3,'translator_Ioff_max_A':ioff,'translator_rail_wide_VOH_load_A':100e-6},'conservative_sufficient_bounds':{'pulldown_actual_max_ohm_for_off_low':r_off_max,'pulldown_actual_min_ohm_for_100uA_high_drive':r_high_min,'nominal_max_ohm_with_1pct':r_off_max/1.01,'nominal_min_ohm_with_1pct':r_high_min/.99,'overlap':r_high_min<=r_off_max},'conclusion':'A pulldown cannot satisfy these two sufficient bounds simultaneously. This does not prove every stronger-drive or alternative circuit impossible. Do not replace U11 based only on the 100uA rail-wide specification.','remaining':['Higher-load VOH coverage across 4.75..5.25V or a different topology','Input-level supply current at actual RAIL_HEALTH_N levels','Partial brownout and propagation before isolation','Whole-circuit fault and sequencing integration'],'electrical_qualification':False}
assert not report['conservative_sufficient_bounds']['overlap']
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report['conservative_sufficient_bounds'],indent=2))
