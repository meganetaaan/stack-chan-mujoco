"""Add independent passive bleeds downstream of both reverse FETs; conditional RC only."""
import argparse,copy,csv,hashlib,json,math
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
files={'base':'schematics/power/servo_power_pololu_integration_candidate_v1/assembly.json','resistor':'schematics/power/passive_discharge_candidate.json','old_plan':'validation/passive_discharge_candidate_v2/plan.json'}
d={k:json.loads(Path(v).read_text()) for k,v in files.items()};base=d['base'];r=d['resistor'];plan=d['old_plan'];out=copy.deepcopy(base)
for side in ['LEFT','RIGHT']:
 for n in [1,2]:out['parts'].append({'reference':f'{side}_R_DISCHARGE_{n}','part':r['proposed_order_code'],'value_ohm':r['resistance_each_ohm'],'pins':{'1':side+'_SERVO_BUS','2':'GND'},'status':'candidate_thermal_resistance_envelope_not_qualified'})
assert out['parts'][:len(base['parts'])]==base['parts'];refs=[p['reference'] for p in out['parts']];assert len(refs)==len(set(refs));byref={p['reference']:p for p in out['parts']}
for side in ['LEFT','RIGHT']:
 for n in [1,2]:assert byref[f'{side}_R_DISCHARGE_{n}']['pins']['1']==byref[side+'_Q_REVERSE']['pins']['5']
R=r['resistance_each_ohm'];tol=plan['assumed_resistance_tolerance'];rmax=R*(1+tol);rmin=R*(1-tol);C=plan['assumed_Cout_max_uF']*1e-6;t=.920;limit=plan['candidate_requirement']['rail_at_920ms_after_disconnect_max_V'];rows=[]
for v0 in [plan['initial_voltage_bound_V'],6.0]:
 for count in [2,1,0]:
  E=math.exp(-t/(rmax/count*C)) if count else 1.;v=v0*E
  rows.append({'initial_V':v0,'surviving_resistors_per_leg':count,'rail_after_920ms_V':v,'conditional_RC_meets_inherited_target':v<=limit,'max_total_capacitance_F_if_no_backfeed':t/((rmax/count)*math.log(v0/limit)) if count else 0.,'max_constant_backfeed_A_for_same_deadline':max(0,(limit-v)/((rmax/count)*(1-E))) if count else 0.})
out.update({'scope':'Dual Pololu power plus per-leg passive discharge candidate; no manufacturing or electrical qualification','part_count':len(refs),'pin_count':sum(len(p['pins']) for p in out['parts']),'manufacturing_release':False})
out['candidate_integration']={'inputs':files,'source_sha256':{k:hashlib.sha256(Path(v).read_bytes()).hexdigest() for k,v in files.items()},'base_parts_unchanged':True,'current_pointer_changed':False,'previous_candidate_integration':base.get('candidate_integration')}
report={'part_count':len(refs),'connections':out['pin_count'],'added_resistors':4,'downstream_of_reverse_FET':True,'left_right_positives_not_connected':True,'rows':rows,'comparison_max_current_per_leg_at5_25V_A':2*5.25/rmin,'comparison_max_total_power_at5_25V_W':4*5.25**2/rmin,'each_resistor_power_at6V_W':6**2/rmin,'capacitance_and_5percent_resistance_are_unqualified_assumptions':True,'bleed_is_not_regenerative_brake':True,'manufacturing_release':False}
a.out.mkdir(parents=True,exist_ok=True)
for name,value in [('assembly',out),('report',report)]:(a.out/(name+'.json')).write_text(json.dumps(value,indent=2)+'\n')
with (a.out/'candidate_bom.csv').open('w',newline='') as f:
 w=csv.writer(f,lineterminator='\n');w.writerow(['reference','part','status'])
 for p in out['parts']:w.writerow([p['reference'],p.get('part'),'candidate_not_released' if p.get('part') else 'unselected'])
print(json.dumps(report,indent=2))
