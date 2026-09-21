"""TPSM63610 divider-only screening; not total load/line regulation qualification."""
import argparse,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
# 0.1% initial resistor tolerance is an explicit comparison assumption.
tol=.001;top=100000.;bottom=25000.;bias=50e-9
lo=.985*(1+top*(1-tol)/(bottom*(1+tol)))-bias*top*(1+tol)
hi=1.015*(1+top*(1+tol)/(bottom*(1-tol)))+bias*top*(1+tol)
wire=json.loads(Path('validation/servo_wire_selection_v1/report.json').read_text())
model=json.loads(Path('validation/model_dc_envelope_v1/report.json').read_text())
efuse=json.loads(Path('schematics/power/main_efuse_candidate.json').read_text())
drop=wire['nominal_wire_plus_post_environment_contact_drop_V']+model['per_leg_draw_upper_A']*efuse['ron_max_ohm_at_2A_specified_temperature']
r={'candidate':'TPSM63610RDFR x2, isolated left/right 5V outputs','source':'https://www.ti.com/lit/ds/symlink/tpsm63610.pdf','revision':'SLVSGU1A December 2023','continuous_nameplate_A':8,'peak_nameplate_A':10,'reference_range_V':[.985,1.015],'divider_ohm':[top,bottom],'initial_resistor_tolerance':tol,'FB_bias_comparison_A':bias,'divider_only_output_range_V':[lo,hi],'remaining_drop_to_4_75V':lo-4.75,'remaining_after_existing_branch_and_efuse_comparison_V':lo-4.75-drop,'per_leg_model_draw_A':model['per_leg_draw_upper_A'],'manufacturing_release':False,'pending':['Exact resistor total tolerance and drift','Line/load regulation, ripple, load steps and dropout at selected 2S minimum','PCB thermal design and enclosure cooling','Reverse current, input absent, per-rail regeneration and protection','Input/output capacitors effective values, layout and complete BOM'],'decision':'Retain dual-module precision alternative; not single-module 12-axis continuous supply'}
(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
