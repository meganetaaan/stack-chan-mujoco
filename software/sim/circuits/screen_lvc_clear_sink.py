"""DC tradeoff screen only; no claim of complete reset-interface qualification."""
import argparse,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
# Preserve the earlier comparison target; leakage at differing datasheet test
# conditions remains a comparison assumption, not a newly proven guarantee.
vmin,vmax=3.207,3.393
high_target=2.69695
rows=[]
for r in (100000,82000,75000):
 low_load=vmax/(r*.99)+4e-6+.3e-6
 high=vmin-r*1.01*(4e-6+.3e-6+2e-6)
 rows.append(dict(resistance_ohm=r,sink_load_A=low_load,high_comparison_V=high,
                  below_100uA=low_load<=100e-6,meets_unchanged_high_comparison=high>=high_target))
report=dict(candidate='74LVC1G06GW',source='https://assets.nexperia.com/documents/data-sheet/74LVC1G06.pdf',revision='16.1, 2024-09-03',rows=rows,
 low_output_spec=dict(max_V=.1,load_A=100e-6,supply_V=[1.65,5.5]),
 comparison_high_target_V=high_target,proposed_pullup_ohm=75000,
 input_low_max_V=.8,input_high_min_V=2.,input_transition_max_ns_per_V=10,
 integrated=False,electrical_qualification=False,
 pending=['Receiver thresholds over actual rail interval',
          'Leakage guarantees at actual rail and input states',
          'Drive edge rate including open-driver pullup and power transitions',
          'Clear pulse, recovery, observation and sequencing hardware'])
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
