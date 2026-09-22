"""Bound health-node loading conditionally; never infer full power-up qualification."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
source=ROOT/'schematics/power/protected_pack_system_candidate_v6/assembly.json'
a=json.loads(source.read_text());p={q['reference']:q for q in a['parts']}
net='SYS__RAIL_HEALTH_N'
endpoints={(q['reference'],pin) for q in a['parts'] for pin,n in q['pins'].items() if n==net}
expected={('SYS__U7','3'),('SYS__U9','1'),('SYS__U11','2'),('SYS__R9','2')}|{(f'SYS__{s}_U_WINDOW',pin) for s in ('LEFT','RIGHT') for pin in ('1','6')}
assert endpoints==expected
assert p['SYS__R9']['part']=='TNPW060310K0BEEA' and p['SYS__R9']['value_ohm']==10000
# Conservative loading at 0V; includes all four off-output leakages even if one sinks.
rlo,rhi=9900.,10100.
leak=4*300e-9+300e-9+1e-6
imax=3.6/rlo+3.6/70000+leak
# Ignore internal MR pullup assistance for high calculation.
high3=3.-rhi*leak
report={
 'source_sha256':{str(source.relative_to(ROOT)):hashlib.sha256(source.read_bytes()).hexdigest()},
 'node_endpoints':[{'reference':ref,'pin':pin} for ref,pin in sorted(endpoints)],
 'criteria_before_calculation':{'single_sink_must_carry_entire_node_load':True,'no_parallel_sink_credit':True,'MR_low_at3V_max_V':.9,'Schmitt_falling_at3V_min_V':.88,'MR_high_at3V_min_V':2.1,'Schmitt_rising_at3V_max_V':1.71},
 'engineering_conditions':{'rail_loading_max_V':3.6,'DC_receiver_comparison_V':3.,'R9_total_tolerance':.01,'leakage_magnitudes_used_over_node_range':'comparison allocation; catalog conditions listed below','additional_board_leakage_A':0},
 'source_limits':{'TPS3700_each_OD_leak_A':300e-9,'TPS3700_leak_conditions':'VDD1.8/18V,VO=VDD;VDD1.8V,VO18V','TPS3808_reset_leak_A':300e-9,'TPS3808_reset_leak_condition':'VRESET6.5V,reset not asserted','LVC1G17_input_leak_A':1e-6,'LVC1G17_leak_condition':'VI5.5V orGND,VCC0..5.5V','TPS3808_MR_pullup_min_ohm':70000},
 'node_leak_allocation_A':leak,'node_sink_load_A_upper_comparison':imax,
 'single_sink_rows':[
 {'part':'TPS3700DDCR','catalog_VDD_V':1.8,'catalog_sink_A':.003,'catalog_VOL_max_V':.25,'current_headroom_A':.003-imax,'MR_low_margin_at3V_V':.9-.25,'Schmitt_low_margin_at3V_V':.88-.25},
 {'part':'TPS3808G33DBVR','catalog_VDD_range_V':[1.8,6.5],'catalog_sink_A':.001,'catalog_VOL_max_V':.4,'current_headroom_A':.001-imax,'MR_low_margin_at3V_V':.9-.4,'Schmitt_low_margin_at3V_V':.88-.4}],
 'released_high_at3V_comparison_V':high3,'MR_high_margin_at3V_V':high3-2.1,'Schmitt_high_margin_at3V_V':high3-1.71,
 'decision':'Keep10k candidate: merged fan-in is not excessive in this static comparison. Do not reduce resistor or add parallel sinks to pass.',
 'sources':[{'url':'https://www.ti.com/lit/ds/symlink/tps3700.pdf','revision':'G February2019','section':'6.5'}, {'url':'https://www.ti.com/lit/ds/symlink/tps3808.pdf','revision':'N August2026','section':'6.5'}, {'url':'https://assets.nexperia.com/documents/data-sheet/74LVC1G17.pdf','revision':'16.1 September2024','section':'10,10.1'}],
 'remaining':['TPS3700 VOL table points are not an explicit3.3V minimum/maximum sweep; static comparison is not full PVT proof','Intermediate/off-supply leakage and retained charge','Node capacitance and transient response,450us monitor startup validity','STOP_AUX/SYS rail ordering and reset/enable clearing below valid supplies','Actual board leakage and selected resistor total drift budget'],
 'complete_static_envelope_qualified':False,'transient_executed':False,'manufacturing_release':False}
assert all(q['current_headroom_A']>0 and q['MR_low_margin_at3V_V']>0 and q['Schmitt_low_margin_at3V_V']>0 for q in report['single_sink_rows'])
assert report['MR_high_margin_at3V_V']>0 and report['Schmitt_high_margin_at3V_V']>0
out=ROOT/'validation/health_node_static_v1';out.mkdir(exist_ok=True)
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'sink_load_comparison_A':imax,'high_at3V_V':high3,'fully_qualified':False}))
