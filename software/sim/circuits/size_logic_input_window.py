"""Nominal TPS26600 logic-branch window; distinct from cell undervoltage protection."""
import argparse,itertools,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
plan={'source':'https://www.ti.com/lit/gpn/tps2660 SLVSDG2G Table7.5','purpose':'Logic LDO functional supply window only, not 3S cell protection.','manufacturer_inputs':{'UV_rising_V':[1.175,1.225],'UV_falling_V':[1.08,1.125],'OV_rising_V':[1.17,1.225],'OV_falling_V':[1.085,1.125],'sense_leakage_A':[-1e-7,1e-7]},'engineering_choices':{'UV_top_ohm':40200,'OV_top_ohm':124000,'bottom_ohm':10000,'total_resistor_tolerance':.01},'criteria_before_calculation':['UV falling minimum above 4.3V TPS709 nominal+1V input reference','UV rising maximum below 12.6V full battery','OV rising minimum above 12.6V full battery','OV rising maximum below 30V TPS709 recommended input maximum; static condition only'],'limits':['No minimum battery operating voltage established by this check','Threshold source table has 24V common test condition; 3S applicability still requires review','No dynamic overshoot, source impedance, failure or component qualification','Do not infer per-cell undervoltage protection from pack window'],'stop':'One divider pair; no threshold sweep.'}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');rows={}
for name,rt in [('UV',40200),('OV',124000)]:
 for direction in ['rising','falling']:
  vs=[v*(1+r/b)+i*r for v,r,b,i in itertools.product(plan['manufacturer_inputs'][name+'_'+direction+'_V'],[rt*.99,rt*1.01],[9900,10100],[-1e-7,1e-7])]
  rows[name+'_'+direction+'_V']=[min(vs),max(vs)]
checks={'UV_falling_above_4V3':rows['UV_falling_V'][0]>4.3,'UV_rising_below_full_battery':rows['UV_rising_V'][1]<12.6,'OV_rising_above_full_battery':rows['OV_rising_V'][0]>12.6,'OV_rising_below_LDO_limit':rows['OV_rising_V'][1]<30}
r={'ranges':rows,'static_conditional_checks':checks,'qualified':False,'dividers_battery_current_upper_A':12.6/(.99*(40200+10000))+12.6/(.99*(124000+10000))}
assert all(checks.values())
(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
