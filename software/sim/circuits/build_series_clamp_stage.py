"""Build the pin-level LT4363-1 alternative branch, keeping unresolved interfaces explicit."""
import argparse,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
pins={'1':'FB','2':'OUT','3':'SNS','4':'GATE','5':'VCC','6':'SHDN','7':'GND','8':'UV','9':'GND','10':'FLT','11':'ENOUT','12':'TMR'}
parts=[]
def add(ref,part,connections,**kwargs):parts.append({'ref':ref,'part':part,'pins':connections,**kwargs})
for side in ['L','R']:
 def net(x):return 'GND' if x=='GND' else f'{side}_{x}'
 mapping={'FB':'FB','OUT':'SHUNT_LOW','SNS':'SHUNT_HIGH','GATE':'GATE','VCC':'SOURCE_5V','SHDN':'SHDN_PORT','GND':'GND','UV':'UV_PORT','FLT':'FLT_PORT','ENOUT':'ENOUT_PORT','TMR':'TMR'}
 add(f'U_{side}','LT4363IMS-1#PBF',{n:net(mapping[role]) for n,role in pins.items()},pin_roles=pins)
 add(f'Q_{side}','PSMN2R4-30YLD',{**{str(i):net('SHUNT_HIGH') for i in [1,2,3]},'4':net('GATE'),'mb':net('SOURCE_5V')},status='SOA unverified; illustrative topology only')
 for i,ends in enumerate([('SHUNT_HIGH','SHUNT_MID'),('SHUNT_MID','SHUNT_LOW')],1):
  add(f'RS_{side}{i}','WSLF25124L000FEA',{'1':net(ends[0]),'2':net(ends[1])},value_ohm=.004)
 add(f'RFBH_{side}',None,{'1':net('SHUNT_LOW'),'2':net('FB')},value_ohm=33200,total_tolerance_allocation=.01)
 add(f'RFBL_{side}',None,{'1':net('FB'),'2':'GND'},value_ohm=10000,total_tolerance_allocation=.01)
 add(f'CTMR_{side}',None,{'1':net('TMR'),'2':'GND'},value_F=12e-9,status='capacitance proposal; actual part and timing bound pending')
 add(f'CVCC_{side}',None,{'1':net('SOURCE_5V'),'2':'GND'},value_F=100e-9,status='bypass proposal; actual part and input transient pending')
by={x['ref']:x for x in parts}
for side in ['L','R']:
 u=by[f'U_{side}']['pins'];q=by[f'Q_{side}']['pins']
 assert u['7']==u['9']=='GND' # -1 variant: pin7 is GND, not -2 OV.
 assert u['3']==q['1']==by[f'RS_{side}1']['pins']['1']
 assert u['2']==by[f'RS_{side}2']['pins']['2']
 assert u['5']==q['mb'] and u['4']==q['4']
 assert by[f'RS_{side}1']['pins']['2']==by[f'RS_{side}2']['pins']['1']
report={'controller_source':'https://www.analog.com/media/en/technical-documentation/data-sheets/4363fb.pdf','revision':'C',
 'scope':'Alternative two-branch series clamp; not integrated into current revM and not ready to energize.',
 'parts':parts,'ports_per_branch':['SOURCE_5V','SHUNT_LOW','SHDN_PORT','UV_PORT','FLT_PORT','ENOUT_PORT'],
 'checks':{'pin7_variant_ground':True,'sense_across_two_resistors':True,'source_supply_and_gate_path':True},
 'interface_constraints':['SHDN and UV ports require defined drivers/dividers before use; never leave this draft as a working circuit.',
 'FLT and ENOUT are outputs requiring selected pullups/receivers; they are not interchangeable with existing PG.',
 'VCC follows regulator source, not battery; changing this alters timer behavior.',
 'Single pass FET body diode allows reverse load-to-source current; separate reverse blocking and downstream regeneration absorption still required.',
 'Kelvin SNS/OUT connections must follow layout error budget.'],
 'missing':['UV divider and fail-safe SHDN interface','FLT/ENOUT receiver and rearm integration','Gate damping/stability review','Input/output capacitors and transients','FET SOA and timer maximum','Reverse blocking and regeneration integration'],
 'electrical_qualification':False,'manufacturing_release':False}
a.out.mkdir(parents=True,exist_ok=False);(a.out/'assembly.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'parts':len(parts),'pins':sum(len(x['pins']) for x in parts),'checks':report['checks']}))
