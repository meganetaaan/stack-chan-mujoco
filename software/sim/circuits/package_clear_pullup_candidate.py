"""Create a reviewable R14-only assembly candidate; do not switch current pointer."""
import argparse, copy, csv, hashlib, json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
base=Path('schematics/power/servo_power_rearm_integration_revM/assembly.json')
edge=Path('validation/sequence_clear_edge_v1/report.json')
old=json.loads(base.read_text());new=copy.deepcopy(old)
report=json.loads(edge.read_text());row=next(x for x in report['rows'] if x['R_ohm']==1000)
assert row['conditional_budget_pass'] and not report['manufacturing_release']
parts={x['reference']:x for x in new['parts']};r=parts['R14']
assert r['part'].startswith('100k') and r['pins']=={'1':'LOGIC3V3','2':'SEQUENCE_CLEAR_REQUEST'}
selected=parts['R_STOP_INPUT'];assert selected['part']=='TNPW12061K00BYEA'
r.update(part=selected['part'],value_ohm=1000,total_tolerance_budget=.01,status='conditional_release_edge_candidate_not_qualified',source=str(edge))
new['scope']=__doc__
new['integration_limitations'] += ['R14 1k candidate assumes total node capacitance <=50pF, common rail 3.207..3.393V and leakage <=13.58uA excluding board leakage. None is a PCB qualification.', 'Budget up to 3.428mA continuous GPIO sink while request Low and 11.63mW resistor dissipation. Whole rail/current budget incomplete.', 'Startup controller remains unimplemented. This change is not power-transition, reset or protection qualification.']
new['source_sha256']={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in [base,edge]}
changes=[x['reference'] for x,y in zip(old['parts'],new['parts']) if x!=y]
assert changes==['R14'] and len(new['parts'])==len(old['parts'])
assert all(x['pins']==y['pins'] for x,y in zip(old['parts'],new['parts']))
a.out.mkdir(parents=True,exist_ok=False)
(a.out/'assembly.json').write_text(json.dumps(new,indent=2)+'\n')
with (a.out/'candidate_bom.csv').open('w') as f:
 w=csv.writer(f,lineterminator='\n');w.writerow(['reference','part_candidate','value_ohm','value_F'])
 for x in new['parts']:w.writerow([x['reference'],x['part'],x.get('value_ohm',''),x.get('value_F','')])
result={'changed_parts':changes,'pin_connections_unchanged':True,'part_count':len(new['parts']),'pin_count':sum(len(x['pins']) for x in new['parts']),'edge_evidence':str(edge),'manufacturing_release':False,'current_pointer_changed':False}
(a.out/'change_report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
