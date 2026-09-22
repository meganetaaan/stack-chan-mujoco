"""Connect both servo enables after checking settled drive and clamp loading."""
import argparse,copy,hashlib,itertools,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
src=Path('schematics/power/servo_power_rearm_integration_revC/assembly.json')
thresholds=Path('schematics/power/integrated_enable_interface.json')
r=copy.deepcopy(json.loads(src.read_text()));spec=json.loads(thresholds.read_text())
plan={'logic_rail_V':[3.207,3.393],'stop_rail_required_V':[3.207,3.393],
 'series_ohm':4700,'pulldown_ohm':39000,'resistor_total_tolerance_assumption':.01,
 'buffer_high_drop_V':.1,'buffer_high_test_current_A':100e-6,
 'clamp_leak_high_max_A':300e-9,'clamp_low_max_V':.4,'clamp_low_test_current_A':.001,
 'scope':'Settled supply and correctly asserted command/clamp only; no power sequence or fault pulse claim',
 'criteria':'High above 1.224V within 100uA drive; asserted clamp below 1.073V within 1mA sink; no enable above recommended 5V'}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
rows=[];pin_leak=2*spec['pin_leakage_abs_max_A']
for v,rs,rp in itertools.product(plan['logic_rail_V'],[4653,4747],[38610,39390]):
 vo=v-.1
 en=(vo/rs-pin_leak-plan['clamp_leak_high_max_A'])/(1/rs+1/rp)
 drive=(vo-en)/rs
 rows.append({'logic_V':v,'series_ohm':rs,'pulldown_ohm':rp,'enable_high_min_V':en,'high_drive_A':drive})
clamp_i=max(plan['logic_rail_V'])/4653+pin_leak
high=min(x['enable_high_min_V'] for x in rows)
# Upper voltage is bounded using rail maximum, pullup-side leakage and divider.
high_upper=(3.393/4653+pin_leak+plan['clamp_leak_high_max_A'])/(1/4653+1/39390)
assert high>spec['thresholds_V']['rising_max']
assert max(x['high_drive_A'] for x in rows)<100e-6
assert clamp_i<.001 and .4<spec['thresholds_V']['falling_min']
assert high_upper<spec['thresholds_V']['recommended_max']
parts={x['reference']:x for x in r['parts']}
for side in ('LEFT','RIGHT'):
 assert parts[side+'_U_POWER']['pins']['1']==side+'_EN_UVLO'
 parts[side+'_U_POWER']['pins']['1']='MAIN_EFUSE_EN'
 r['interfaces'].pop(side+'_EN_UVLO',None)
r['interfaces']['MAIN_EFUSE_EN']='Common logic enable to both TPS259813L pin1; source UV/OV monitoring remains external and unimplemented'
r['scope']=__doc__;r['source_sha256']={str(q):hashlib.sha256(q.read_bytes()).hexdigest() for q in (src,thresholds)}
r['integration_limitations']=[s for s in r['integration_limitations'] if not s.startswith('MAIN_EFUSE_EN is deliberately') and s!='EN_UVLO drive remains unimplemented']
r['integration_limitations'] += ['Common EN drive is connected and statically screened; startup/brownout behavior and source UV monitoring unqualified','One common EN trace is not independent fault-tolerant shutdown; output and wiring faults require analysis']
r['electrical_qualification']=False;r['manufacturing_release']=False
(a.out/'assembly.json').write_text(json.dumps(r,indent=2)+'\n')
report={'rows':rows,'minimum_enable_high_V':high,'maximum_enable_high_comparison_V':high_upper,
 'asserted_clamp_current_upper_A':clamp_i,'asserted_clamp_off_margin_V':spec['thresholds_V']['falling_min']-.4,
 'settled_interface_pass':True,'full_default_off_qualified':False,'manufacturing_release':False}
(a.out/'enable_report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='rows'}))
