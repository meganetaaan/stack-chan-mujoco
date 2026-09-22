"""Static interface and incremental supply budget; no ramp/fault qualification."""
import argparse,hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parents[3]
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
paths=['schematics/power/aux_start_isolator_candidate.json','schematics/power/system_power_integration_candidate_v1/assembly.json','validation/stop_supply_budget_v1/report.json']
c,assembly,old=[json.loads((root/x).read_text()) for x in paths]
parts={x['reference']:x for x in assembly['parts']};iso=parts['SYS__U_AUX_START_ISO']['pins']
assert iso['4']=='CELL_B_MINUS' and iso['5']=='PACK_RETURN'
assert iso['1']==iso['3']=='BQ_CTRL3V3' and iso['8']=='SYS__STOP_AUX3V3'
assert iso['2']==parts['BAT__U_BQ_AUX_GATE']['pins']['4']
assert iso['6']==parts['SYS__R_LOGIC_SHDN_SER']['pins']['1']
e=c['electrical_screen'];tol=.01
rp=parts['BAT__R_BQ_AUX_START_REQUEST_PD']['value_ohm']
rser=parts['SYS__R_LOGIC_SHDN_SER']['value_ohm'];rpd=parts['SYS__R_LOGIC_SHDN_PD']['value_ohm']
primary_load=3.6/(rp*(1-tol))+e['ISO_input_current_testpoint_abs_A']
secondary_load=e['secondary_supply_conditional_V'][1]/((rser+rpd)*(1-tol))
high=(e['secondary_supply_conditional_V'][0]-e['ISO_VOH_drop_V'])*rpd*(1-tol)/(rpd*(1-tol)+rser*(1+tol))
# Evaluate pull-down capacity at the specified 0.4V SHDN boundary, rather than
# extrapolating the internal source's I-V curve to an invented lower voltage.
low_sink=(.4-e['ISO_VOL_max_V'])/(rser*(1+tol))+.4/(rpd*(1+tol))
report={'source_sha256':{x:hashlib.sha256((root/x).read_bytes()).hexdigest() for x in paths},
 'primary_AND_output_load_comparison_A':primary_load,
 'primary_AND_low_current_testpoint_A':100e-6,
 'primary_high_margin_min_V':3.0-.15-.7*3.0,
 'secondary_SHDN_high_min_comparison_V':high,
 'secondary_sink_capacity_at_SHDN0_4V_A':low_sink,
 'SHDN_internal_source_at0_4V_requirement_A':10e-6,
 'secondary_output_load_comparison_A':secondary_load,
 'primary_DC_addition_max_under_source_conditions_A':e['ISO_ICC1_DC_max_high_A'],
 'secondary_DC_addition_comparison_A':e['ISO_ICC2_DC_max_high_A']+secondary_load,
 'old_STOP_budget_is_conditional_A':old['conditional_DC_sum_A'],
 'updated_STOP_DC_comparison_A':old['conditional_DC_sum_A']+e['ISO_ICC2_DC_max_high_A']+secondary_load,
 'STOP_feed_drop_comparison_at_plus1percent_V':(1/sum(1/parts['SYS__R_STOP_INPUT_'+str(i)]['value_ohm'] for i in range(2)))*1.01*(old['conditional_DC_sum_A']+e['ISO_ICC2_DC_max_high_A']+secondary_load),
 'functional_states':[
  {'primary':'valid','secondary':'valid','input':0,'output':0},
  {'primary':'valid','secondary':'valid','input':1,'output':1},
  {'primary':'off','secondary':'valid','input':'irrelevant','output':0},
  {'primary':'valid','secondary':'valid','input':'open','output':0},
  {'primary':'any','secondary':'off_or_ramping','input':'any','output':'whole_branch_inhibit_not_qualified'}],
 'conditions':['Both rails within3.3V +/-10% and all listed IC test conditions','Resistor total variation+/-1% is an allocation','Input leakage test points are not arbitrary intermediate-level bounds','Inherited STOP budget is unqualified and omits startup, some loading and leakage','No transient or actual precharge load bound is established'],
 'bootstrap_supply_dependency_removed_topologically':True,
 'electrical_qualification':False,'manufacturing_release':False}
assert primary_load<100e-6 and high>1 and low_sink>10e-6
assert secondary_load<.002
a.out.mkdir(parents=True,exist_ok=True);(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
