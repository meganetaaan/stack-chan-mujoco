"""Export candidate OVP and manual-permission connectivity, without ERC claims."""
import argparse,csv,hashlib,json
from collections import defaultdict
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
files={'manual':Path('schematics/power/manual_rearm_revI/assembly.json'),'ovp':Path('schematics/power/servo_ovp_revA/connectivity.json')}
nets=defaultdict(list);rows=[];refs=set()
for group,path in files.items():
 data=json.loads(path.read_text())
 for part in data['parts']:
  ref=part.get('reference',part.get('ref'));unique=group+':'+ref
  if unique in refs:raise ValueError('Duplicate reference '+unique)
  refs.add(unique)
  pins=part.get('pins',part.get('pin_nets'))
  if pins is None:raise ValueError('Missing pin map '+unique)
  for pin,net in pins.items():
   row={'assembly':group,'ref':ref,'part':part['part'],'pin':pin,'net':net or 'NC'};rows.append(row)
   if net:nets[net].append({'assembly':group,'ref':ref,'pin':pin})
# Report unresolved interfaces explicitly; a source or load is not inferred
# merely because multiple terminals share a net.
required={}
for side in ['L','R']:
 for name,why in [('OV_SENSE','OV divider absent'),('UV_SENSE','UV divider absent'),('FAULT_N','Fault receiver absent'),('UBEC','UBEC connector and distribution not implemented'),('OV_OUT','Overcurrent stage not instantiated in this connection table')]:
  key=name+'_'+side;required[key]={'connections':nets[key],'missing':why}
report={'source_sha256':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in files.values()},'parts':len(refs),'pins':len(rows),'nets':dict(nets),'cross_assembly_nets':{n:v for n,v in nets.items() if len({x['assembly'] for x in v})>1},'required_unimplemented_interfaces':required,'electrical_rule_check':False,'manufacturing_release':False,'scope':'Connection export only; no component behavioral model, power-state or fault qualification'}
with (a.out/'pins.csv').open('w',newline='') as stream:
 writer=csv.DictWriter(stream,fieldnames=['assembly','ref','part','pin','net']);writer.writeheader();writer.writerows(rows)
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'parts':len(refs),'pins':len(rows),'cross_assembly_nets':list(report['cross_assembly_nets']),'unimplemented_interfaces':len(required)}))
