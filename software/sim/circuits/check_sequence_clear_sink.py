"""Source-derived static comparison for the revH open-drain clear driver."""
import argparse,json,hashlib
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
root=Path(__file__).resolve().parents[3]
spec=root/'schematics/power/sequence_clear_sink_candidate.json'
d=json.loads(spec.read_text());old=json.loads((root/'schematics/power/manual_rearm_revG/assembly.json').read_text());new=json.loads((root/'schematics/power/manual_rearm_revH/assembly.json').read_text())
refs={p['reference']:p for p in new['parts']}
assert all(refs[p['reference']]==p for p in old['parts'])
assert len(refs)==new['part_count']
rail_min,rail_max=d['logic_supply_V'];rmin=100000*.99;rmax=100000*1.01
report={'source_sha256':hashlib.sha256(spec.read_bytes()).hexdigest(),'prior_40_part_connections_unchanged':True,
'input_open_high_comparison_V':rail_min-.75e-6*rmax,
'input_low_driver_sink_upper_A':rail_max/rmin+.75e-6,
'reset_high_lower_comparison_V':rail_min-(4e-6+.3e-6+d['off_output_leak_A_max_125C'])*rmax,
'reset_low_sink_upper_A':rail_max/rmin+4e-6+.3e-6,
'low_output_test_current_A':d['low_output_comparison']['test_sink_A'],
'low_output_max_comparison_V':d['low_output_comparison']['vol_V_max'],
'no_claims':['whole-rail threshold qualification','edge and propagation timing','power-loss default assertion','full fault-clearing implementation'],
'manufacturing_release':False}
assert report['input_open_high_comparison_V']>d['input_assert_high_V_min']
assert report['reset_low_sink_upper_A']<report['low_output_test_current_A']
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
