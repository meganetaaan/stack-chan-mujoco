"""Route source window faults to existing reset latch; connectivity proof only."""
import copy,csv,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
src=ROOT/'schematics/power/protected_pack_system_candidate_v4/assembly.json'
out=ROOT/'schematics/power/protected_pack_system_candidate_v5'
val=ROOT/'validation/source_window_reset_connection_v1'
for p in (out,val):p.mkdir(exist_ok=True)
a=json.loads(src.read_text()); r=copy.deepcopy(a)
p={x['reference']:x for x in r['parts']}
assert p['SYS__U7']['pins']['3']=='SYS__RAIL_HEALTH_N'
assert p['SYS__U7']['pins']['1']=='SYS__RESET_N'
assert p['SYS__U6']['pins']['1']==p['SYS__U6']['pins']['13']=='SYS__RESET_N'
assert p['SYS__U3']['pins']['5']=='SYS__RESET_N'
old_endpoints={};removed=[]
for side in ('LEFT','RIGHT'):
 net=f'SYS__{side}_SOURCE_WINDOW_OD';ref=f'SYS__{side}_U_WINDOW';pu=f'SYS__{side}_R_WINDOW_PULLUP'
 endpoints=[{'reference':q['reference'],'pin':pin} for q in a['parts'] for pin,n in q['pins'].items() if n==net]
 assert {(x['reference'],x['pin']) for x in endpoints}=={(ref,'1'),(ref,'6'),(pu,'2')}
 old_endpoints[net]=endpoints
 assert p[ref]['part']=='TPS3700DDCR'
 assert p[ref]['pins']['5']=='SYS__STOP_AUX3V3'
 assert p[pu]['pins']=={'1':'SYS__STOP_AUX3V3','2':net}
 p[ref]['pins']['1']=p[ref]['pins']['6']='SYS__RAIL_HEALTH_N'
 removed.append(pu)
r['parts']=[q for q in r['parts'] if q['reference'] not in removed]
assert len(r['parts'])==194
# Keep just the existing health pullup; do not join two supply rails with pullups.
assert p['SYS__R9']['pins']=={'1':'SYS__LOGIC3V3','2':'SYS__RAIL_HEALTH_N'}
changed=[q['reference'] for q in a['parts'] if q['reference'] not in removed and q['pins']!=p[q['reference']]['pins']]
assert changed==['SYS__LEFT_U_WINDOW','SYS__RIGHT_U_WINDOW']
report={'source_sha256':{str(src.relative_to(ROOT)):hashlib.sha256(src.read_bytes()).hexdigest()},
 'prior_unconsumed_window_endpoints':old_endpoints,'changed_pin_maps':changed,'removed_pullups':removed,
 'retained_pullup':'SYS__R9 to SYS__LOGIC3V3',
 'path':['TPS3700 OUTA or OUTB low','SYS__RAIL_HEALTH_N low','SYS__U7 MR low','SYS__RESET_N low','SYS__U6 asynchronous latch clear and SYS__U3 permission gate low'],
 'operating_truth_cases':[{'left_valid':l,'right_valid':rr,'other_health_released':h,'health_can_release':l and rr and h} for l in (False,True) for rr in (False,True) for h in (False,True)],
 'sources':[{'url':'https://www.ti.com/lit/ds/symlink/tps3700.pdf','revision':'G February2019','sections':['5 DDC pinout','7.3 open-drain outputs']}],
 'design_decision':'Require both pre-eFuse regulator voltages valid before servo permission; source faults clear manual rearm latch. Regulator startup request must remain independent of SYS reset to avoid startup deadlock.',
 'limits':['Connectivity and ideal valid-supply truth table only; not transient or timing simulation',
 'Merged health node leakage/capacitance, VOL and receiver margins must be recomputed',
 'STOP_AUX startup/loss and TPS3700 startup delay require qualification',
 'Regulator commands still unconnected; manual rearm and source qualification timings incomplete',
 'Existing window thresholds and downstream response need whole-chain fault evaluation'],
 'electrically_qualified':False,'manufacturing_release':False}
r['source_window_reset_connection']=report
r['status']='source_window_reset_connected_candidate_not_operational'
r['checks'].pop('unique196references',None);r['checks']['unique194references']=True
r['checks']['source_window_reset_path_connected']=True
r['source_sha256']=report['source_sha256']
r['remaining'].append('Requalify merged health node and start regulators independently of SYS reset')
(out/'assembly.json').write_text(json.dumps(r,indent=2)+'\n')
(val/'report.json').write_text(json.dumps(report,indent=2)+'\n')
for name,header,rows in [('bom.csv',['reference','part','group'],[[x['reference'],x.get('part'),x.get('integration_group')] for x in r['parts']]),('connections.csv',['reference','pin','net'],[[x['reference'],pin,net] for x in r['parts'] for pin,net in x['pins'].items()])]:
 with (out/name).open('w',newline='') as f:
  w=csv.writer(f,lineterminator='\n');w.writerow(header);w.writerows(rows)
print(json.dumps({'references':len(r['parts']),'changed_pin_maps':changed,'removed':removed,'qualified':False}))
