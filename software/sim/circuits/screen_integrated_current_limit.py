"""Conditional RILM sizing: normal load margin and fast-trip exposure, not coordination proof."""
import argparse,itertools,json,hashlib
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
load_path=next(Path('validation/model_dc_envelope_v2').glob('*.json'))
# Locate authoritative field rather than silently substitute a different aggregate.
for candidate in Path('validation/model_dc_envelope_v2').glob('*.json'):
 d=json.loads(candidate.read_text())
 if 'per_leg_draw_upper_A' in d:load_path=candidate;load=d['per_leg_draw_upper_A'];break
else:raise ValueError('Per-leg load field missing')
rows=[]
for resistor in [1100.]:
 lo=6585/(resistor*1.001)*.9;hi=6585/(resistor*.999)*1.1
 rows.append({'RILM_nominal_ohm':resistor,'nominal_limit_A':6585/resistor,'comparison_min_limit_A':lo,'comparison_max_limit_A':hi,'model_normal_margin_A':lo-load,'scalable_fast_trip_comparison_max_A':hi*2.42})
r={'rows':rows,'per_leg_model_draw_A':load,'source_load_sha256':hashlib.sha256(load_path.read_bytes()).hexdigest(),'source':'https://www.ti.com/lit/ds/symlink/tps25981.pdf','resistor_initial_tolerance':.001,'IC_accuracy_comparison_fraction':.10,'assumptions':['6585/R nominal relation and +/-10 percent sizing comparison above 5A; not full characterization of selected variant','Initial resistor tolerance only, no lifetime drift','Fast-trip ratio maximum 242 percent from electrical table; not steady allowed load','Existing model load is not measured hardware peak'],'manufacturing_release':False,'coordination_qualified':False}
(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(rows))
