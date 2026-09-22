"""Static specification check for HCS11 -> LVC1G34 -> TPS3808 MR."""
import argparse,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
plan={'scope':__doc__,'criteria':'Load within published DC test-current limits; positive worst-case high/low margins on assumed 3.207..3.393 V rail. No dynamic or startup claim.','stop':'One analytical corner evaluation; no waveform sweep.'}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
vmin,vmax=3.207,3.393
r={'assumed_rail_V':[vmin,vmax],'HCS_to_buffer':{'buffer_leakage_max_A':2e-6,'HCS_test_current_A':20e-6,'high_margin_V':vmin-.1-2,'low_margin_V':.8-.1},'buffer_to_MR':{'sink_current_upper_A':vmax/70000,'buffer_test_current_A':100e-6,'high_margin_V':.3*vmin-.1,'low_margin_V':.3*vmin-.1},'assumptions':['Common valid rail at all three parts','HCS input logic conditions already met','No extra output load','Datasheet DC output limits used for lower load current'],'unverified':['HCS input thresholds and raw interface','LVC input transition maximum 10 ns/V','power sequencing and brownout','independent stop and default-off output']}
r['DC_interface_pass']=all([r['HCS_to_buffer']['buffer_leakage_max_A']<=20e-6,r['HCS_to_buffer']['high_margin_V']>0,r['HCS_to_buffer']['low_margin_V']>0,r['buffer_to_MR']['sink_current_upper_A']<=100e-6,r['buffer_to_MR']['high_margin_V']>0,r['buffer_to_MR']['low_margin_V']>0]);r['circuit_release']=False
(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
