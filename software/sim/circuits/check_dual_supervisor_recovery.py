"""Construct a settled threshold-mismatch counterexample for revD alone."""
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
root=Path(__file__).resolve().parents[3]
src=root/'schematics/power/manual_rearm_revD/assembly.json'
assembly=json.loads(src.read_text());parts={x['reference']:x for x in assembly['parts']}
assert parts['U7']['pins']['1']=='RESET_N'
assert parts['U9']['pins']['1']=='MAIN_EFUSE_EN'
assert parts['U6']['pins']['13']=='RESET_N'
plan={'question':'Does revD alone cancel retained permission whenever its independent clamp stops power?', 'acceptance':'After undervoltage causes EN shutdown, supply recovery alone must not restore EN', 'assumptions':['Previously accepted enable request remains at POWER_ENABLE_COMMAND unless explicitly cleared','U7 falling threshold at allowed low endpoint; U9 at allowed high endpoint','Supply dip is settled at 3.07V, not a timing model','Recovery to3.3V is observed after both release delays settle','eFuse input5V remains valid'], 'stop':'One permitted threshold counterexample; no random or transient sweep', 'assembly_sha256':hashlib.sha256(src.read_bytes()).hexdigest()}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
low,high=3.07*.985,3.07*1.015
assert low<3.07<high
permission=True
rows=[]
for name,v in [('enabled',3.3),('settled_dip',3.07),('settled_recovery_no_press',3.3)]:
 clear=v<low;clamp=v<high
 if clear:permission=False
 rows.append({'event':name,'logic_supply_V':v,'U7_clear':clear,'U9_clamp':clamp,'retained_permission':permission,'EN_high_boolean_after_settling':permission and not clamp,'new_press':False})
assert not rows[1]['EN_high_boolean_after_settling'] and rows[2]['EN_high_boolean_after_settling']
r={'U7_falling_V':low,'U9_falling_V':high,'trace':rows,'revD_alone_no_auto_restart':'FAIL','complete_future_sequencer':'not_evaluated_or_implemented','required_resolution':'A clamp/power-loss event must latch a stop and clear permission; PG sequencing can provide coverage only with verified timing and pulse capture; no direct EN-to-RESET_N tie.'}
(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
