"""Put one pull-down at each eFuse EN pin, retaining near-original normal load."""
import argparse,copy,hashlib,itertools,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
src=Path('schematics/power/servo_power_rearm_integration_revD/assembly.json')
r=copy.deepcopy(json.loads(src.read_text()));parts={x['reference']:x for x in r['parts']}
assert parts['R5']['pins']=={'1':'MAIN_EFUSE_EN','2':'GND'}
r['parts']=[x for x in r['parts'] if x['reference']!='R5']
for side in ('LEFT','RIGHT'):
 node=side+'_EN_LOCAL';parts[side+'_U_POWER']['pins']['1']=node
 r['parts'].append({'reference':side+'_R_EN_PULLDOWN','part':None,'value_ohm':78700,'total_tolerance_budget':.01,'pins':{'1':node,'2':'GND'},'placement':'At eFuse EN pin and local ground, after monitored trace; no shared remote pulldown'})
 r['interconnects'].append({'name':side+'_EN_TRACE','from':'MAIN_EFUSE_EN','to':node,'type':'PCB trace, not a resistor','placement':'Local pulldown on eFuse side of trace break'})
rows=[]
for v,rs,rl,rr in itertools.product([3.207,3.393],[4653,4747],[77913,79487],[77913,79487]):
 g=1/rs+1/rl+1/rr
 high=((v-.1)/rs-.5e-6)/g
 drive=((v-.1)-high)/rs
 rows.append({'supply_V':v,'series_ohm':rs,'left_ohm':rl,'right_ohm':rr,'high_min_V':high,'drive_A':drive})
assert min(x['high_min_V'] for x in rows)>1.224
assert max(x['drive_A'] for x in rows)<100e-6
open_node_max=79487*.1e-6
assert open_node_max<.45
r['scope']=__doc__;r['part_count']=len(r['parts']);r['pin_count']=sum(len(x['pins']) for x in r['parts'])
r['source_sha256']={str(src):hashlib.sha256(src.read_bytes()).hexdigest()}
r['integration_limitations']+=['Local EN pull-downs replace R5; earlier 39k calculations are historical','Open trace analysis is settled leakage only; discharge timing and pin/pulldown ground faults unqualified']
r['manufacturing_release']=False
(a.out/'assembly.json').write_text(json.dumps(r,indent=2)+'\n')
report={'removed_reference':'R5','local_pull_down_ohm_each':78700,'normal_parallel_nominal_ohm':39350,
 'rows':rows,'high_min_V':min(x['high_min_V'] for x in rows),'driver_max_A':max(x['drive_A'] for x in rows),
 'open_branch_EN_upper_V':open_node_max,'open_branch_basis':'TPS259813L specified EN leakage +/-0.1uA, local resistor total +/-1%, eFuse powered; excludes parasitic leakage and transients',
 'placement_required':True,'part_count':r['part_count'],'pin_count':r['pin_count'],'manufacturing_release':False}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='rows'}))
