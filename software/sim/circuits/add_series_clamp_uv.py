"""Add a candidate UV divider without equating rising and falling threshold guarantees."""
import argparse,hashlib,itertools,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
source=Path('schematics/power/series_clamp_stage_revA/assembly.json');r=json.loads(source.read_text())
rt,rb,tol=24900,10000,.01
cases=[v*(1+top/bot)+i*top for v,top,bot,i in itertools.product([1.24,1.31],[rt*(1-tol),rt*(1+tol)],[rb*(1-tol),rb*(1+tol)],[-1e-6,1e-6])]
fall=[(v-.012)*(1+top/bot)+i*top for v,top,bot,i in itertools.product([1.24,1.31],[rt*(1-tol),rt*(1+tol)],[rb*(1-tol),rb*(1+tol)],[-1e-6,1e-6])]
for side in ['L','R']:
 u=next(x for x in r['parts'] if x['ref']==f'U_{side}');assert u['pins']['8']==f'{side}_UV_PORT';u['pins']['8']=f'{side}_UV'
 for ref,pins,value in [(f'RUVH_{side}',{'1':f'{side}_SOURCE_5V','2':f'{side}_UV'},rt),(f'RUVL_{side}',{'1':f'{side}_UV','2':'GND'},rb)]:
  r['parts'].append({'ref':ref,'part':None,'pins':pins,'value_ohm':value,'total_tolerance_allocation':tol,'status':'resistor specification proposal; actual part pending'})
r['ports_per_branch'].remove('UV_PORT')
r['interface_constraints'][0]='SHDN requires a defined driver before use. UV divider is connected but cutoff/startup qualification remains incomplete.'
r['missing'][0]='UV thresholds/hysteresis and fail-safe SHDN interface qualification'
r['source_sha256']={str(source):hashlib.sha256(source.read_bytes()).hexdigest()}
r['uv_screen']={'rising_source_threshold_comparison_V':[min(cases),max(cases)],
 'falling_with_typical_hysteresis_only_V':[min(fall),max(fall)],
 'normal_5V_above_rising_max':5>max(cases),
 'guaranteed_falling_threshold_V':None,
 'limits':['1.24..1.31 V rising threshold and +/-1uA input use datasheet VCC12V default; actual 4..5V applicability unqualified.',
 '12mV hysteresis is typical only; do not claim cutoff above 4V from this calculation.',
 '1% total resistor tolerance is allocated, not verified selected-part stability.',
 'Actual converter minimum and transient droop must exceed rising threshold with system margin.']}
r['checks']['UV_has_two_resistor_DC_path']=all(any(p['ref']==f'RUVH_{side}' for p in r['parts']) for side in ['L','R'])
a.out.mkdir(parents=True,exist_ok=False);(a.out/'assembly.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r['uv_screen']))
