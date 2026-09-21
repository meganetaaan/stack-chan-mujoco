"""Check static EN drive conditions without extending Ioff to brownout."""
import argparse,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
plan={'question':'Can a 74LVC1G17 output drive eFuse EN with a passive pulldown?', 'stop':'Static powered and zero-supply comparison, then identify the unqualified intermediate supply interval', 'assumptions':['LOGIC3V3 3.207..3.393V','39k output and 220k input pulldowns with provisional total +/-1% budgets','TPS25982 EN leakage 0.1uA used bidirectionally as conservative comparison at its specified test conditions','Nexperia Ioff 2uA at VCC=0 and VI or VO=5.5V is a published test point, not a brownout model'], 'acceptance':'Powered levels must meet EN thresholds within output load rating; no full default-off claim without intermediate-rail and transient evidence'}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
rmin,rmax=39000*.99,39000*1.01
load=3.393/rmin+.1e-6
r={'output_load_upper_A':load,'output_test_current_A':100e-6,'powered_high_lower_V':3.207-.1,'enable_rising_max_V':1.23,'powered_high_margin_V':3.207-.1-1.23,'powered_low_upper_V':.1,'shutdown_threshold_min_V':.59,'powered_low_margin_V':.59-.1,'zero_supply_leakage_comparison_V':(2e-6+.1e-6)*rmax,'zero_supply_shutdown_margin_comparison_V':.59-(2e-6+.1e-6)*rmax,'input_pulldown_plus_buffer_leakage_A':3.393/(220000*.99)+1e-6,'unqualified_supply_interval_V':[0,1.65],'full_default_off_qualified':False}
assert load<100e-6
assert r['powered_high_margin_V']>0 and r['powered_low_margin_V']>0
assert r['zero_supply_shutdown_margin_comparison_V']>0
(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
