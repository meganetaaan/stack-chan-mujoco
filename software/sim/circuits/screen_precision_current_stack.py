"""Refresh a precision-supply comparison with current protection and bleed loads."""
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
files={'plan':'validation/precision_supply_current_stack_v1/plan.json','wiring':'validation/pololu_wiring_budget_v1/plan.json','motor':'validation/model_dc_envelope_v2/report.json','assembly':'schematics/power/servo_power_pololu_discharge_candidate_v1/assembly.json','bleed':'schematics/power/passive_discharge_candidate.json'}
d={k:json.loads(Path(v).read_text()) for k,v in files.items()};c=d['plan'];w=d['wiring'];parts={x['reference']:x for x in d['assembly']['parts']}
for side in ['LEFT','RIGHT']:
 assert parts[side+'_U_POWER']['part']=='TPS259813LRPW'
 assert parts[side+'_Q_REVERSE']['part'].startswith('SiSS80DN')
 for n in [1,2]:assert parts[f'{side}_R_DISCHARGE_{n}']['value_ohm']==360
T=c['divider_top_ohm'];B=c['divider_bottom_ohm'];e=c['resistor_initial_comparison_tolerance'];b=c['bias_comparison_A']
lo=c['reference_range_V'][0]*(1+T*(1-e)/(B*(1+e)))-b*T*(1+e)
hi=c['reference_range_V'][1]*(1+T*(1+e)/(B*(1-e)))+b*T*(1+e)
# Preserve the previous conservative5.25V bleed-current envelope, not nominal5V.
bleedI=2*5.25/(360*.95);I=d['motor']['per_leg_draw_upper_A']+bleedI
feederR=2*c['wire_case_mm_one_way']/1000*w['wire_comparison']['nominal_DCR_ohm_per_1000ft_at20C']/304.8
commonR=w['efuse_comparison_ohm']+w['reverse_fet_comparison_ohm']+feederR
rows=[]
for axis in d['motor']['rows']:
 drop=I*commonR+axis['dc_draw_upper_A']*2*w['EH_contact_ohm_each']
 rows.append({'axis':axis['model'],'known_comparison_drop_V':drop,'precision_remaining_lower_margin_V':lo-drop-c['terminal_range_V'][0],'Pololu_remaining_lower_margin_V':4.85-drop-c['terminal_range_V'][0],'excluded':'OEM wire, PCB, solder, extra auxiliaries, drift, hot resistance and transient droop'})
r={'source_sha256':{k:hashlib.sha256(Path(v).read_bytes()).hexdigest() for k,v in files.items()},'divider_only_output_V':[lo,hi],'upper_margin_before_ripple_transients_V':c['terminal_range_V'][1]-hi,'shared_comparison_current_A':I,'rows':rows,'decision':'Reopen unchanged5V precision module as design alternative; no manufacturing selection or CAD substitution','qualification':False}
a.out.mkdir(parents=True,exist_ok=True);(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
