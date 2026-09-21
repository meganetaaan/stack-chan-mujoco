"""Check U11 output to U10 MR at settled STOP_AUX3V3, not startup behavior."""
import hashlib,json
from pathlib import Path
src=Path('schematics/power/servo_power_rearm_integration_revB/assembly.json')
a=json.loads(src.read_text());parts={p['reference']:p for p in a['parts']}
assert parts['U11']['pins']['5']==parts['U10']['pins']['6']=='STOP_AUX3V3'
assert parts['U11']['pins']['4']==parts['U10']['pins']['3']=='CLAMP_MR_STOP_AUX'
plan={'supply_interval_V':[3.207,3.393],'supply_interval_status':'Existing conservative design interval; LDO load/transient qualification pending',
 'TPS3808_MR_pullup_min_ohm':70000,'MR_VIH_fraction':.7,'MR_VIL_fraction':.3,
 'buffer_VOH_drop_max_V':.1,'buffer_VOL_max_V':.1,'buffer_test_current_A':100e-6,
 'scope':'U11 output stage and U10 MR only; assumes U11 input already valid',
 'sources':['https://www.ti.com/lit/ds/symlink/tps3808.pdf','https://assets.nexperia.com/documents/data-sheet/74LVC1G17.pdf'],
 'criteria':'Both same-supply logic margins positive and worst MR pullup load below the 100uA output specification'}
rows=[]
for v in plan['supply_interval_V']:
 rows.append({'supply_V':v,'high_margin_V':v-.1-.7*v,'low_margin_V':.3*v-.1,'MR_pullup_sink_upper_A':v/70000})
assert all(r['high_margin_V']>0 and r['low_margin_V']>0 and r['MR_pullup_sink_upper_A']<100e-6 for r in rows)
r={'rows':rows,'settled_output_interface_pass':True,'minimum_margin_V':min(min(x['high_margin_V'],x['low_margin_V']) for x in rows),
 'full_stop_function_qualified':False,'source_sha256':{str(src):hashlib.sha256(src.read_bytes()).hexdigest()},
 'remaining':['U9 output and U11 input threshold qualification','Startup, partial-power and rail-collapse behavior','Dynamic pin current/capacitance and independent stop timing','Total STOP_AUX3V3 load, capacitors and LDO thermal budget']}
out=Path('validation/stop_aux_mr_levels_v1');out.mkdir(exist_ok=True)
(out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');(out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
