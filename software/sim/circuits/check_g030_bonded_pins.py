"""Validate G030 TSSOP20 pin ownership, including physically bonded aliases."""
import argparse,json,hashlib
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
src=Path('schematics/power/sequence_controller_candidate/g030_controller.json');r=json.loads(src.read_text())
expected={'1':{'PB7','PB8'},'2':{'PC14','PB9'},'15':{'PA8','PB0','PB1','PB2'},'19':{'PA14','PA15'},'20':{'PB6','PB3','PB4','PB5'}}
modes={}
for n,x in r['pins'].items():
 if 'bonded_gpios' not in x:continue
 assert set(x['bonded_gpios'])==expected.get(n,{x['selected_gpio']})
 assert x['selected_gpio'] in x['bonded_gpios']
 for gpio in x['bonded_gpios']:
  assert gpio not in modes
  modes[gpio]='analog'
 if x['role']!='spare':modes[x['selected_gpio']]=x['role']
def valid(config):
 for x in r['pins'].values():
  if 'bonded_gpios' not in x:continue
  for gpio in x['bonded_gpios']:
   required=x['role'] if gpio==x['selected_gpio'] and x['role']!='spare' else 'analog'
   if config.get(gpio)!=required:return False
 return True
assert valid(modes)
rejected=[]
for x in r['pins'].values():
 for gpio in x.get('inactive_bonded_gpios',[]):
  corrupt=dict(modes);corrupt[gpio]='output'
  assert not valid(corrupt);rejected.append(gpio)
assert modes['PA13']==modes['PA14']=='debug'
assert all(modes[x]=='analog' for x in expected['20'])
report={'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),
 'gpio_mode_contract':modes,'injected_alias_conflicts_rejected':rejected,
 'spare_pin_all_bonded_ports_analog':True,'pin_ownership_pass':True,
 'implementation_verified':False,'manufacturing_release':False,
 'limits':['Checks the intended mode contract, not register writes or ROM boot behavior',
 'Pulls, analog switches, RTC domain and boot option bytes require implementation',
 'No substitute for input/output electrical or partial-power verification']}
a.out.mkdir(parents=True,exist_ok=False);(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(len(rejected),len(modes))
