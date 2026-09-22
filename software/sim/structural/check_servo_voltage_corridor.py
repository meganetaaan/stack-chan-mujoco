"""Necessary setpoint window under an explicitly conditional transient comparison."""
import argparse, hashlib, json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
source=Path('schematics/power/pol_module_screen.json');module=json.loads(source.read_text())
ov=module['design_comparison']['normal_OV_trip_min_V'];delta=module['load_step_peak_deviation_V']
# Existing engineering rail target; no substitution with servo absolute operating floor.
rail_min=4.75
rows=[]
for drop in [0.,.1]:
    low=rail_min+delta+drop;high=ov-delta
    rows.append({'assumed_distribution_drop_V':drop,'minimum_setpoint_V':low,'exclusive_maximum_setpoint_V':high,'window_width_V':high-low,'nonempty':low<high})
r={'rows':rows,'normal_rail_min_V':rail_min,'normal_rail_basis':'Existing Codex engineering target in PLAN_ja.md, not user requirement or servo manufacturer minimum','transient_comparison_V':delta,'transient_basis':'Module typical at specified load step; not actual robot bound','manufacturing_release':False,'decision':'Lowering setpoint alone cannot accommodate this symmetric transient comparison while preserving current normal rail target, even with zero distribution loss. Do not change rail target just to pass.','sources_sha256':{str(q):hashlib.sha256(q.read_bytes()).hexdigest() for q in [source,Path('docs/prototype/engineering/PLAN_ja.md')]}}
(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(rows))
