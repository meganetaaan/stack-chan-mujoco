"""Compare one- and two-ended EH branches without inventing OEM wire resistance."""
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
s=Path('validation/model_dc_envelope_v2/report.json');r=json.loads(s.read_text())
rows=[]
for total in [3.,r['per_leg_draw_upper_A']]:
 for axis in r['rows']:
  current=axis['dc_draw_upper_A']
  for count in [2,4]:
   contact=current*count*.020;fuse=total*.0084
   residual=.1-contact-fuse
   rows.append({'shared_current_A':total,'axis':axis['model'],'branch_current_A':current,
    'loop_contact_count':count,'contact_drop_V':contact,'efuse_drop_comparison_V':fuse,
    'residual_from_historical_0_10V_budget_V':residual,
    'max_remaining_series_loop_resistance_if_no_other_losses_ohm':max(0,residual/current),
    'budget_already_exceeded_without_wire':residual<0,
    'efuse_current_matches_3A_table_condition':total==3.})
report={'source_sha256':{str(s):hashlib.sha256(s.read_bytes()).hexdigest()},
 'sources':{'contact':'https://www.jst-mfg.com/product/pdf/eng/eEH.pdf','efuse':'https://www.ti.com/lit/ds/symlink/tps25981.pdf'},
 'inputs':{'EH_post_environment_contact_ohm':.020,'efuse_comparison_ohm':.0084,'historical_drop_budget_V':.1},
 'rows':rows,'limitations':['0.10 V derives from the earlier 4.85 V supply floor and 4.75 V terminal target; UBEC lower output is not established.',
 '4.917 A and branch currents are conditional model envelopes, not measured hardware maxima.',
 'Applying the 3 A eFuse RON table value at 4.917 A is a comparison assumption.',
 'Wire, feeder, reverse blocking, solder joints and dynamic drops remain outside the calculation.',
 'Negative budget is a design-screen failure at stated assumptions, not proof all real cables fail.'],
 'decision':'Do not prioritize the extra distribution EH connector. Preserve OEM servo crimp and evaluate a cut, strain-relieved soldered distribution end instead; circuit and routing remain unqualified.',
 'manufacturing_release':False}
a.out.mkdir(parents=True,exist_ok=False);(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(rows[-2:]))
