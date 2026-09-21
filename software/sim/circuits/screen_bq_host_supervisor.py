"""Static threshold/load corners. No 100nF-loaded reset timing guarantee."""
import argparse, hashlib, itertools, json
from pathlib import Path
root=Path(__file__).resolve().parents[3]
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
path=root/'schematics/power/bq_local_host_candidate.json';host=json.loads(path.read_text())
s=host['supervisor_candidate'];parts={x['reference']:x for x in host['parts']}
rt=parts['R_BQ_HOST_SUP_TOP']['value_ohm'];rb=parts['R_BQ_HOST_SUP_BOTTOM']['value_ohm']
tol=s['total_resistance_variation_allocation'];v=s['nominal_threshold_V'];vt=s['threshold_fraction'];il=s['sense_current_abs_A']
values=[]
for rtop,rbot,threshold,current in itertools.product([rt*(1-tol),rt*(1+tol)],[rb*(1-tol),rb*(1+tol)],[v*(1-vt),v*(1+vt)],[-il,il]):
 values.append(threshold*(1+rtop/rbot)+current*rtop)
rpu=parts['R_BQ_HOST_NRST']['value_ohm'];effective=1/(1/(rpu*(1-tol))+1/25000)
result={'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
 'corner_count':len(values),'falling_threshold_V':[min(values),max(values)],
 'release_threshold_conservative_max_V':max(values)*(1+s['hysteresis_fraction_max']),
 'headroom_to_conditional_REG1_min3V_V':3-max(values)*(1+s['hysteresis_fraction_max']),
 'falling_threshold_margin_to_MCU_min2V_V':min(values)-2,
 'NRST_external_plus_internal_pullup_min_ohm':effective,
 'NRST_sink_current_at3_6V_upper_resistive_A':3.6/effective,
 'NRST_low_static_margin_at_MCU2V_V':0.3*2-0.4,
 'divider_current_at3_6V_max_A':3.6/((rt+rb)*(1-tol)),
 'total_resistor_variation_is_allocation_not_qualification':True,
 'reset_timing_with100nF_qualified':False,
 'BQ_communication_below3V_qualified':False,
 'independent_fault_shutdown_qualified':False,
 'manufacturing_release':False}
assert result['headroom_to_conditional_REG1_min3V_V']>0
assert effective>=10000
assert parts['U_BQ_HOST_SUP']['pins']['1']==parts['U_BQ_HOST']['pins']['6']
a.out.mkdir(parents=True,exist_ok=True);(a.out/'report.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
