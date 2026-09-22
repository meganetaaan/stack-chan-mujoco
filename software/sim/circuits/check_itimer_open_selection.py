"""Verify explicit open ITIMER selection against actual assembly endpoints."""
import argparse,json,hashlib
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
pointer=json.loads(Path('schematics/power/servo_power_rearm_current.json').read_text());source=Path(pointer['assembly']);r=json.loads(source.read_text());selection=json.loads(Path('schematics/power/itimer_selection.json').read_text())
rows=[]
for ref in selection['references']:
 x=next(x for x in r['parts'] if x['reference']==ref);assert x['part']==selection['part'];net=x['pins']['10']
 endpoints=[(p['reference'],pin) for p in r['parts'] for pin,n in p['pins'].items() if n==net]
 assert endpoints==[(ref,'10')]
 assert all(net not in (link['from'],link['to']) for link in r.get('interconnects',[]))
 rows.append({'reference':ref,'net':net,'endpoints':endpoints,'no_external_component':True})
(a.out/'report.json').write_text(json.dumps({'assembly':str(source),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'checks':rows,'open_topology_verified':True,'nuisance_trip_qualified':False,'fault_energy_qualified':False},indent=2)+'\n');print('Both ITIMER pins have no external connection')
