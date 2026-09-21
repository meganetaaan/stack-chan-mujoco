"""Necessary ratio bounds for a bare OVLO divider; no transient or clamp qualification."""
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--assembly',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
plan={'question':'Can any bare two-resistor divider both trip by the servo limit and keep OVLO within its recommended maximum during the existing 3S pass-through fault?',
 'source':'https://www.ti.com/lit/ds/symlink/tps25981.pdf','revision':'SLVSGG6D September 2026','sections':['6.3','6.5'],
 'manufacturer':{'OVLO_rise_min_V':1.176,'OVLO_rise_max_V':1.224,'OVLO_recommended_max_V':1.5,'OVLO_absolute_max_V':6.5},
 'retained_design_conditions':{'normal_source_max_V':5.25,'servo_max_V':6.,'source_pass_through_fault_V':12.6},
 'classification':'Design limits/fault case retained from prior power reviews; manufacturer pin constraints separate. No new user requirement.',
 'method':'q=1+Rtop/Rbottom, ideal nominal divider, zero leakage (an admitted operating point). These are necessary conditions; tolerance/delay checks cannot repair a failed nominal necessary condition.',
 'stop':'Analytic interval intersection once, then report existing left/right ratio; no resistor sweep or circuit qualification.',
 'assembly_sha256':hashlib.sha256(a.assembly.read_bytes()).hexdigest(),
 'limits':['No guaranteed source fault slew/energy or shutdown time','No clamp or additional monitor considered','Passing these inequalities alone would not establish protection','Absolute maximum is not used as operating allowance']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
m=plan['manufacturer'];d=plan['retained_design_conditions']
normal=d['normal_source_max_V']/m['OVLO_rise_min_V']
trip=d['servo_max_V']/m['OVLO_rise_max_V']
fault=d['source_pass_through_fault_V']/m['OVLO_recommended_max_V']
parts={c['reference']:c for c in json.loads(a.assembly.read_text())['parts']};rows=[]
for side in ['LEFT','RIGHT']:
 top=parts[side+'_R_OV_TOP'];bottom=parts[side+'_R_OV_BOTTOM'];ic=parts[side+'_U_POWER']
 assert top['pins']['2']==bottom['pins']['1']==ic['pins']['2'] and bottom['pins']['2']=='GND'
 assert top['pins']['1']==ic['pins']['5']
 q=1+top['value_ohm']/bottom['value_ohm']
 rows.append({'side':side,'q_nominal':q,'nominal_fault_pin_V':d['source_pass_through_fault_V']/q,
 'largest_source_V_at_pin_recommended_max_nominal':m['OVLO_recommended_max_V']*q,
 'ideal_trip_interval_V':[m['OVLO_rise_min_V']*q,m['OVLO_rise_max_V']*q]})
result={'q_lower_for_normal_operation_strict':normal,'q_upper_to_trip_by_servo_max':trip,
 'q_lower_for_fault_pin_limit':fault,'nominal_necessary_conditions_feasible':max(normal,fault)<=trip,
 'minimum_worst_threshold_if_fault_ratio_satisfied_V':fault*m['OVLO_rise_max_V'],
 'maximum_fault_source_compatible_with_trip_necessary_bound_V':trip*m['OVLO_recommended_max_V'],
 'rows':rows,'decision':'Bare divider cannot meet both retained conditions; select a different sensing/protection topology before ordering OV divider resistors.',
 'electrical_qualification':False}
assert not result['nominal_necessary_conditions_feasible']
(a.out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
