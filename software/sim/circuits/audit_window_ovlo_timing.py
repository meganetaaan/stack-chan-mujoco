"""Bounded timing-evidence audit; illustrative slew budget is not a fault simulation."""
import argparse, hashlib, itertools, json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
source=Path('schematics/power/servo_power_rearm_integration_revN/assembly.json')
r=json.loads(source.read_text());parts={x['reference']:x for x in r['parts']}
rows=[]
for side in ['LEFT','RIGHT']:
 hi=parts[side+'_R_SOURCE_OV_TOP'];lo=parts[side+'_R_SOURCE_OV_BOTTOM']
 assert hi['pins']['2']==side+'_SOURCE_OV_SENSE'
 corners=[]
 for rt,rb,threshold,leak in itertools.product([hi['value_ohm']*.99,hi['value_ohm']*1.01],[lo['value_ohm']*.99,lo['value_ohm']*1.01],[.396,.404],[-15e-9,15e-9]):
  factor=1+rt/rb
  trip=threshold*factor+leak*rt
  corners.append({'trip_V':trip,'source_at_10mV_sense_overdrive_V':trip+.010*factor})
 worst=max(x['source_at_10mV_sense_overdrive_V'] for x in corners)
 # 29us: rising INPUT, falling OUTB. Not 18us (opposite input edge).
 nominal_delays=29e-6+1.2e-6
 rows.append({'side':side,'trip_max_V':max(x['trip_V'] for x in corners),'source_at_test_overdrive_max_V':worst,
 'headroom_to_6V_at_test_overdrive_V':6-worst,
 'illustrative_slew_budget_V_per_s':(6-worst)/nominal_delays})
report={'assembly':str(source),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
 'requirement':'Servo terminal voltage <=6V; unchanged. Source and servo voltage transfer remains unqualified.',
 'sources':[{'url':'https://www.ti.com/lit/ds/symlink/tps3700.pdf','revision':'SBVS187G February 2019','section':'6.6 footnote 1','positive_input_delay_nominal_s':29e-6,'maximum_s':None,'conditions':'VDD=5V, 10mV input overdrive, Rp=10kohm; actual STOP supply differs'},
 {'url':'https://www.ti.com/lit/ds/symlink/tps25981.pdf','revision':'SLVSGG6D September 2026','section':'6.6','OVLO_delay_typical_s':1.2e-6,'maximum_s':None}],
 'rows':rows,'qualified_timing':False,'decision':'Do not adopt revN as the sole fast overvoltage protection path.',
 'limits':['29us and 1.2us are nominal/typical, not worst-case delay bounds. Adding them does not produce an application maximum.',
 'Illustrative slew calculation assumes source rise continues linearly and servo voltage follows source; neither behavior is established.',
 'Inverter delay, output fall, resistor/capacitance delay, switch fall and wiring are omitted: illustration is optimistic even apart from nominal delay uncertainty.',
 '10mV overdrive translates through the existing monitor divider; cannot start the published delay at the comparator threshold without accounting for the test condition.',
 'Input-step feedthrough, regenerated energy and stored load energy require the actual power path; slowing an invented source waveform is not proof.'],
 'next_design_requirement':'Establish a hardware voltage/energy limiting path for converter feedthrough and regeneration, with a bounded fault envelope and response. Window monitor may remain supervisory. Do not move unfinished protection design to physical follow-up.'}
a.out.mkdir(parents=True,exist_ok=False);(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(rows,indent=2))
