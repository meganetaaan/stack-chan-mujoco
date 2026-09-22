"""Join selected comparison power stages to dual PG receivers without inventing enable wiring."""
import argparse,copy,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
lp=Path('schematics/power/manual_rearm_revJ/assembly.json')
pp=Path('schematics/power/integrated_servo_power_revA/connectivity.json')
logic=json.loads(lp.read_text());power=json.loads(pp.read_text())
r=copy.deepcopy(logic)
refs={x['reference'] for x in logic['parts']}
if refs & {x['reference'] for x in power['parts']}:raise ValueError('reference collision')
def nets(parts):return {n for x in parts for n in x['pins'].values() if n}
shared=nets(logic['parts']) & nets(power['parts'])
if shared != {'GND','LEFT_PG_SOURCE','RIGHT_PG_SOURCE'}:raise ValueError(shared)
r['parts']+=copy.deepcopy(power['parts'])
byref={x['reference']:x for x in r['parts']}
checks=[]
for side in ('LEFT','RIGHT'):
 source=side+'_PG_SOURCE';receiver=side+'_EFUSE_PG'
 assert byref[side+'_U_POWER']['pins']['3']==source
 assert byref[side+'_R10']['pins']['2']==source
 assert byref[side+'_R11']['pins']['1']==receiver
 assert any(x['from']==source and x['to']==receiver for x in r['interconnects'])
 checks.append({'side':side,'PG_output':side+'_U_POWER.3','source_pullup':side+'_R10.2','receiver_input':side+'_R11.1','trace_connected':True})
 r['interfaces'].pop(source,None)
 for suffix,description in [('REGULATOR_OUT','External selected converter output, not included'),('SERVO_BUS','Servo branch, regeneration absorber and discharge not included'),('EN_UVLO','External enable/UVLO network, UNIMPLEMENTED'),('FLT_N','Fault output, capture network UNIMPLEMENTED'),('ITIMER','Timer passive not selected')]:
  r['interfaces'][side+'_'+suffix]=description
r['scope']=__doc__
r['part_count']=len(r['parts']);r['pin_count']=sum(len(x['pins']) for x in r['parts'])
r['source_sha256']={str(q):hashlib.sha256(q.read_bytes()).hexdigest() for q in (lp,pp)}
r['integration_limitations']=['MAIN_EFUSE_EN is deliberately not connected to EN_UVLO: drive and UVLO network not designed','Startup sequencer and source-voltage monitors absent','Converter, battery protection, input/output capacitors, regeneration and discharge omitted','Power-stage part values and OVLO fault pin range remain unqualified','Connectivity only: no integrated transient or fault proof']
r['manufacturing_release']=False;r['electrical_qualification']=False
r['power_stage_warnings']=power['warnings']
(a.out/'assembly.json').write_text(json.dumps(r,indent=2)+'\n')
report={'shared_nets':sorted(shared),'PG_checks':checks,'part_count':r['part_count'],'pin_count':r['pin_count'],
 'unselected_parts':[x['reference'] for x in r['parts'] if x.get('part') is None],
 'enable_network_implemented':False,'manufacturing_release':False}
(a.out/'integration_report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
