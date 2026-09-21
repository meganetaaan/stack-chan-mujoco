"""Reference allocations only; datasheet conditions in logic_ic_current_review_v1/v2."""
import json,hashlib,argparse
from pathlib import Path
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
p=Path('schematics/power/servo_power_clear_pullup_candidate_v1/assembly.json');a=json.loads(p.read_text())
types={'MAX6816EUS+T':('4',20),'SN74LVC1G04DBVR':('5',10),'SN74HCS11PWR':('14',2),'SN74HCS74PW':('14',2),'74LVC1G17GV':('5',4),'TPS3808G33DBVR':('6',6),'TPS3808G01DBVR':('6',6),'TPS3700DDCR':('5',13),'74AUP1G06GW':('5',.9),'SN74AUP1T50DCKR':('5',.9)}
rows=[];totals={}
for x in a['parts']:
 if x['part'] not in types:continue
 pin,value=types[x['part']];rail=x['pins'][pin];assert rail in ['LOGIC3V3','STOP_AUX3V3'];totals[rail]=totals.get(rail,0)+value
 rows.append({'reference':x['reference'],'part':x['part'],'supply_pin':pin,'rail':rail,'reference_allocation_uA':value})
r={'source_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'rows':rows,'reference_subtotal_uA':totals,'guaranteed_all_state_bound':False,'limitations':'See README and review_v1 for manufacturer test conditions. MCU, internal button pullup, dynamic current excluded.'}
args.out.write_text(json.dumps(r,indent=2)+'\n');print(len(rows),totals)
