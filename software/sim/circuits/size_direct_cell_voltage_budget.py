"""Necessary loaded-cell voltage for the retained distribution comparison; not a battery cutoff specification."""
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
hp=Path('validation/oem_harness_headroom_v1/report.json');wp=Path('schematics/power/source_window_monitor_revB/report.json');cp=Path('schematics/power/oem_servo_harness_candidate.json')
h=json.loads(hp.read_text());window=json.loads(wp.read_text());cable=json.loads(cp.read_text())
plan={'question':'What loaded source voltage is necessary before unspecified feeder/cable/battery losses, and can the current UV monitor start from a 4.2V single-cell source?',
 'source_sha256':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in [hp,wp,cp]},
 'manufacturer_servo_min_V':3.7,'architecture_comparison_source_max_V':4.2,
 'classification':'3.7V servo minimum is a part constraint; 4.2V source is an unselected architecture assumption, not a selected cell specification.',
 'stop':'Reuse only existing individual-branch two-contact comparison rows; no unknown resistance sweep or cutoff selection.',
 'limits':['OEM cable loop resistance is unspecified','Shared current 4.917A is an old model bound, not measured or hardware limited','eFuse 8.4mohm maximum is specified at 3A; other currents remain comparison','Source voltage is loaded at distribution input, not open-circuit cell voltage','Battery internal resistance, feeder, fuse, reverse switch, solder, dynamics and temperature unallocated']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');rows=[]
for r in h['rows']:
 if r['loop_contact_count']!=2:continue
 known=r['contact_drop_V']+r['efuse_drop_comparison_V']
 rows.append({'shared_current_comparison_A':r['shared_current_A'],'axis':r['axis'],'branch_current_comparison_A':r['branch_current_A'],
 'necessary_loaded_source_V_before_other_losses':3.7+known,'remaining_at_assumed_4p2V_before_other_losses_V':4.2-3.7-known,
 'efuse_current_matches_3A_table_condition':r['efuse_current_matches_3A_table_condition']})
uv=window['results']['UV']['thresholds_V']['rising']
report={'rows':rows,'existing_UV_rising_interval_V':uv,'existing_UV_can_release_by_assumed_4p2V':uv[0]<=4.2,
 'cable_max_loop_resistance_ohm':cable['unknown']['max_loop_resistance_ohm'],
 'additional_drop_formula_V':'I_shared*R_shared_loop + I_branch*R_branch_wire + other protection/connector drops + dynamic allowance',
 'cutoff_selected':False,'battery_selected':False,'existing_board_reusable_unchanged':False,'manufacturing_release':False}
assert not report['existing_UV_can_release_by_assumed_4p2V']
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
