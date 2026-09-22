"""Combine existing branch and eFuse comparisons without treating them as rated maxima."""
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
paths=[Path('validation/servo_wire_selection_v1/report.json'),Path('schematics/power/main_efuse_candidate.json')]
w,e=[json.loads(x.read_text()) for x in paths]
rbranch=w['wire_loop_ohm']+w['contacts_loop_ohm'];ron=e['ron_max_ohm_at_2A_specified_temperature']
rows=[]
for shared in (1.,2.,4.815,6.):
 remaining=.1-rbranch*w['evaluation_current_A']-shared*ron
 rows.append({'shared_current_comparison_A':shared,'branch_current_comparison_A':1.,'branch_drop_V':rbranch,'efuse_drop_comparison_V':shared*ron,'remaining_for_feeder_other_protection_and_dynamics_V':remaining,'feeder_resistance_ceiling_if_no_other_losses_ohm':remaining/shared,'efuse_current_matches_2A_spec_point':shared==2.})
result={'qualified':False,'scope':'stationary-wire comparison applied to star-distribution feasibility only','source_hashes':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},'rows':rows,'limitations':['Wire DCR is nominal at 20C, not a worst-case bound','4.815A is motor-current sum comparison, not DC guarantee','eFuse resistance outside its 2A test point is a comparison assumption','Voltage ripple, reverse isolation, fuse, common connectors and hot-wire resistance remain unallocated'],'decision':'Do not release full-robot distribution using this 0.10V budget; select exact common path and dynamic-load bound before further sequencer integration'}
(a.out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
