"""Select order-table resistor candidates without changing values or threshold budgets."""
import argparse, hashlib, json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--out',type=Path,required=True)
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
base=Path('schematics/power/servo_power_rearm_integration_revI/assembly.json')
r=json.loads(base.read_text())
codes={10000:'10K0',100000:'100K',102000:'102K',130000:'130K',220000:'220K'}
refs=[f'{side}_{name}' for side in ('LEFT','RIGHT') for name in ('R_SOURCE_UV_TOP','R_SOURCE_UV_BOTTOM','R_SOURCE_OV_TOP','R_SOURCE_OV_BOTTOM','R_WINDOW_PULLUP')]
refs+=['R_MONITOR_START','R_MONITOR_RX_OFF','R_SEQUENCE_OFF']
# Preconditions/criteria are fixed before computing: 1% total budget retained,
# 0.1% initial, 10 ppm/K over -40..85 C conditional film temperature.
plan={'source':'https://www.vishay.com/docs/28758/tnpw_e3.pdf','revision':'10-Apr-2026 pp2-4',
 'initial_tolerance':0.001,'TCR_ppm_K':10,'conditional_film_temperature_C':[-40,85],
 'reference_temperature_C':20,'existing_total_budget':0.01,
 'power_screen_voltage_V':12.6,'general_mode_P70_W':0.11,
 'conditional_ambient_max_C':85,'general_mode_film_limit_C':125,
 'criteria':['Nominal values and connections unchanged','Initial plus temperature contribution below existing 1% budget','12.6 V across each resistor below voltage and derated power limits'],
 'limits':['12.6 V is the selected 3S full-charge comparison, not a transient bound',
 'Actual PCB film temperature, soldering and ageing remain to qualify',
 'Order-table candidates do not establish stock or small-quantity availability',
 'No IC fault tolerance or circuit transient qualification follows from resistor power screening']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
rows=[]
for part in r['parts']:
 if part['reference'] not in refs: continue
 assert part['part'] is None
 value=part['value_ohm'];assert value in codes
 part['part']='TNPW0603'+codes[value]+'BYEA'
 part['selection_source']=str(a.out/'plan.json')
 part['total_tolerance_budget']=0.01
 initial_temp=0.001+10e-6*max(abs(t-20) for t in (-40,85))
 power=12.6**2/(value*(1-0.01))
 allowed=.11*(125-85)/(125-70)
 assert initial_temp<.01 and power<allowed and 12.6<100
 rows.append({'reference':part['reference'],'part':part['part'],'value_ohm':value,
 'initial_plus_temperature_fraction':initial_temp,'remaining_unallocated_fraction':.01-initial_temp,
 'power_screen_W':power,'derated_power_limit_W':allowed})
assert len(rows)==len(refs)==13
r['scope']='Assign manufacturer order-table candidates to 13 monitor/default resistors; values unchanged'
r['source_sha256']={str(base):hashlib.sha256(base.read_bytes()).hexdigest()}
r['integration_limitations'].append('13 monitor/default resistor ordering codes selected; total tolerance ageing/process and PCB thermal verification remain pending; EA packaging 5000 pieces')
(a.out/'assembly.json').write_text(json.dumps(r,indent=2)+'\n')
(a.out/'resistor_report.json').write_text(json.dumps({'parts':rows,'count':len(rows),'conditional_screen_pass':True,'manufacturing_release':False},indent=2)+'\n')
print('13 resistors selected; conditional tolerance/power screen passed')
