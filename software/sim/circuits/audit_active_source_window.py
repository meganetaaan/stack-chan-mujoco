"""Bind converter comparison criteria to the actual current integrated circuit."""
import argparse,hashlib,json,math
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
ptr=Path('schematics/power/servo_power_rearm_current.json');pointer=json.loads(ptr.read_text());assembly_path=Path(pointer['assembly']);assembly=json.loads(assembly_path.read_text());parts={p['reference']:p for p in assembly['parts']}
monitor_plan=Path('schematics/power/source_window_monitor_revB/plan.json');monitor_report=Path('schematics/power/source_window_monitor_revB/report.json');efuse_report=Path('validation/integrated_ov_divider_v1/report.json');module_path=Path('schematics/power/pol_module_screen.json')
mp=json.loads(monitor_plan.read_text());mr=json.loads(monitor_report.read_text());ef=json.loads(efuse_report.read_text());module=json.loads(module_path.read_text())
plan={'question':'Which normal-source targets and static trip comparisons actually apply to the current pointer?',
 'stop':'Read current part values, validate referenced divider calculations, then compute necessary setpoint ranges. No part selection or threshold changes.',
 'limits':['Static thresholds are comparison results with recorded tolerance assumptions, not full fault-response qualification','Normal target is Codex engineering assumption, not converter guarantee or user requirement','Typical transient is a comparison case, not a worst-case guarantee','Monitor recovery alone does not prove whole-sequence restart']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
for side in ['LEFT','RIGHT']:
 for suffix,value in [('OV_TOP',35700),('OV_BOTTOM',10000)]:
  part=parts[side+'_R_'+suffix];assert part['value_ohm']==value and part['initial_tolerance_comparison']==.001
 for mode in ['UV','OV']:
  for suffix,value in [('TOP',mp[mode+'_top_ohm']),('BOTTOM',mp['bottom_ohm'])]:
   part=parts[side+'_R_SOURCE_'+mode+'_'+suffix];assert part['value_ohm']==value and part['total_tolerance_budget']==mp['resistor_total_tolerance_assumption']
# Check archived eFuse corner rows really use the current nominal values.
for row in ef['corners']:
 assert any(math.isclose(row['Rhigh_ohm'],35700*k) for k in [.999,1.001])
 assert any(math.isclose(row['Rlow_ohm'],10000*k) for k in [.999,1.001])
 trip=row['reference_V']*(1+row['Rhigh_ohm']/row['Rlow_ohm'])+row['leak_A']*row['Rhigh_ohm']
 assert math.isclose(trip,row['trip_V'],abs_tol=1e-10)
no_trip=min(ef['trip_range_V'][0],mr['results']['OV']['thresholds_V']['rising'][0]);normal_low,normal_high=mp['normal_source_comparison_V'];delta=module['load_step_peak_deviation_V'];rows=[]
for drop in [0.,.1]:
 low=normal_low+delta+drop;high=normal_high-delta;trip_high=no_trip-delta
 rows.append({'distribution_drop_assumption_V':drop,'minimum_setpoint_V':low,'maximum_setpoint_from_normal_target_V':high,'exclusive_maximum_setpoint_from_static_trip_V':trip_high,'normal_target_window_nonempty':low<=high,'static_trip_window_nonempty':low<trip_high})
files=[ptr,assembly_path,monitor_plan,monitor_report,efuse_report,module_path]
result={'source_sha256':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},'active_revision':pointer['revision'],'divider_values_match_current':True,'normal_source_target_V':[normal_low,normal_high],'static_earliest_OV_trip_comparison_V':no_trip,'source_monitor_OV_recovery_min_only_V':mr['results']['OV']['thresholds_V']['falling'][0],'historical_trip_not_current_V':module['design_comparison']['normal_OV_trip_min_V'],'module_typical_symmetric_step_comparison_V':delta,'rows':rows,'manufacturing_release':False,'remaining_fault_limits':ef['limits']}
(a.out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['source_sha256','remaining_fault_limits']},indent=2))
