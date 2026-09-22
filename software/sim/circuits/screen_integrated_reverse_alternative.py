"""Bounded rejection screen: integrated RCB avoids gate unknowns but costs headroom."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
paths={'wire':'validation/pololu_wiring_budget_v1/plan.json','load':'validation/model_dc_envelope_v2/report.json','module':'schematics/power/dual_pololu_candidate.json','gate':'validation/pololu_reverse_gate_review_v1/report.json'}
d={k:json.loads((ROOT/v).read_text()) for k,v in paths.items()}
source_min=d['module']['output_V']*(1-d['module']['accuracy_fraction'])
floor=d['wire']['inherited_engineering_target_V']
i=d['load']['per_leg_draw_upper_A']
assert i==4.917
bleed=5.25/(360*.95)*2
rows=[]
for axis in d['load']['rows']:
 branch=axis['dc_draw_upper_A'];contacts=branch*d['wire']['contacts_each_branch_loop']*d['wire']['EH_contact_ohm_each']
 for resistance,kind in [(0.0122,'typical12V25C, not qualification'),(.020,'catalog20mohm at3A over3.5..23V,-40..125C; extrapolation to leg current is comparison only')]:
  loss=(i+bleed)*resistance+contacts
  rows.append({'axis':axis['model'],'resistance_ohm':resistance,'condition':kind,'shared_current_A':i+bleed,'contacts_drop_V':contacts,'efuse_drop_V':(i+bleed)*resistance,'remaining_V_before_wire_and_PCB':source_min-floor-loss,'efuse_loss_W_comparison':(i+bleed)**2*resistance})
assert all(q['remaining_V_before_wire_and_PCB']<0 for q in rows if q['resistance_ohm']==.02)
r={'sources':[
 {'url':'https://www.ti.com/lit/ds/symlink/tps25948.pdf','revision':'D April2026','sections':['4 latch-off TPS259480LYWP','6.5 RON','7.3.5 reverse protection']},
 {'url':'https://www.ti.com/lit/ds/symlink/tps25981.pdf','revision':'D September2026','section':'7.3.9 external gate driver'}],
 'source_sha256':{v:hashlib.sha256((ROOT/v).read_bytes()).hexdigest() for v in paths.values()},
 'candidate':'TPS259480LYWP latch-off integrated reverse-blocking alternative; procurement suffix not selected',
 'source_min_V':source_min,'retained_engineering_floor_V':floor,'total_drop_budget_V':source_min-floor,
 'bleed_comparison_A':bleed,'rows':rows,
 'decision':'Do not substitute one TPS25948 per leg in current5V module/OEM-contact topology. Typical-only calculation hides negative worst-case comparison margin.',
 'gate_RC_decision':'Existing loaded VGS and turnoff bounds remain missing. Do not choose arbitrary RC then infer gate suitability. No circuit change made.',
 'next_design_options':['Split lower-current protected servo groups and account extra protection/discharge/wiring hardware','Choose a converter with tighter guaranteed5V output accuracy while retaining terminal upper/lower limits','Qualify existing external gate driver with authoritative limits; RC alone does not supply those limits'],
 'limits':['20mohm specified at3A is not proof of actual4.948A hot resistance; screening only','Contact resistance and bleed are inherited engineering comparison conditions','No wire/PCB/hot contact loss or transient droop included','No thermals, inrush, reverse response, SOA or fault qualification','Integrated reverse blocker does not absorb regeneration; downstream energy handling still required'],
 'qualified':False,'manufacturing_release':False}
out=ROOT/'validation/integrated_reverse_alternative_v1';out.mkdir(exist_ok=True)
(out/'report.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps({'rows':rows,'decision':r['decision']}))
