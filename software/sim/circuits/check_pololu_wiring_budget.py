"""Account common-rail and individual branch losses without conflating currents."""
import argparse,json,hashlib
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
files={'plan':'validation/pololu_wiring_budget_v1/plan.json','module':'schematics/power/dual_pololu_candidate.json','assembly':'schematics/power/servo_power_pololu_integration_candidate_v1/assembly.json','load':'validation/model_dc_envelope_v2/report.json'}
d={k:json.loads(Path(v).read_text()) for k,v in files.items()};cfg=d['plan'];m=d['module'];parts={x['reference']:x for x in d['assembly']['parts']}
for side in ['LEFT','RIGHT']:
 q=parts[side+'_Q_REVERSE'];assert q['part'].startswith('SiSS80DN')
 assert q['pins']['1']==side+'_INTERNAL_OUT' and q['pins']['5']==side+'_SERVO_BUS'
 assert parts[side+'_U_POWER']['part'].startswith('TPS259813L')
I=d['load']['per_leg_draw_upper_A'];assert I==m['design_comparison_current_A_per_leg']
source_min=m['output_V']*(1-m['accuracy_fraction']);budget=source_min-cfg['inherited_engineering_target_V']
rho=cfg['wire_comparison']['nominal_DCR_ohm_per_1000ft_at20C']/304.8
rows=[]
for axis in d['load']['rows']:
 i=axis['dc_draw_upper_A'];fixed=I*(cfg['efuse_comparison_ohm']+cfg['reverse_fet_comparison_ohm'])+i*cfg['contacts_each_branch_loop']*cfg['EH_contact_ohm_each']
 for length in cfg['wire_comparison']['one_way_lengths_mm']:
  feeder=I*2*length/1000*rho;residual=budget-fixed-feeder
  rows.append({'axis':axis['model'],'shared_current_A':I,'branch_current_A':i,'feeder_one_way_mm':length,'fixed_drop_V':fixed,'feeder_nominal_drop_V':feeder,'remaining_V':residual,'remaining_branch_loop_ohm_if_all_other_losses_zero':max(0,residual/i),'max_feeder_one_way_mm_if_branch_wire_and_all_other_losses_zero':max(0,(budget-fixed)/(2*I*rho)*1000),'status':'comparison_budget_exceeded' if residual<0 else 'unqualified_positive_residual'})
w=cfg['wire_comparison'];report={'source_sha256':{k:hashlib.sha256(Path(v).read_bytes()).hexdigest() for k,v in files.items()},'source_min_V':source_min,'total_drop_budget_V':budget,'one_reverse_FET_per_leg_confirmed_in_current_assembly':True,'rows':rows,'wire_geometry_only':{'OD_max_mm':(w['OD_inch']+w['OD_tolerance_inch'])*25.4,'bend_radius_at_max_OD_mm':5*(w['OD_inch']+w['OD_tolerance_inch'])*25.4,'not_dynamic_flex_qualification':True},'limits':cfg['unmodelled_losses'],'manufacturing_release':False}
a.out.mkdir(parents=True,exist_ok=True);(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
