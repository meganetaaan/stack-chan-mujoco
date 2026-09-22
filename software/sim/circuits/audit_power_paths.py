"""Enumerate connectivity of shared absorber candidate after power-path cuts."""
import json
from pathlib import Path
p=Path('validation/power_path_state_audit_v1')
plan=json.loads((p/'plan.json').read_text())
# Source disconnect is upstream of the protected servo distribution rail.
edges=[('source','bus'),('bus','source'),('bus','absorber')]
for i in range(12):
 edges += [('bus',f'branch{i}'),(f'branch{i}','bus'),(f'branch{i}',f'servo{i}'),(f'servo{i}',f'branch{i}')]
cases={
 'normal':[],
 'source_disconnected':[('source','bus'),('bus','source')],
 'branch0_protection_open':[('bus','branch0'),('branch0','bus')],
 'servo0_cable_detached':[('branch0','servo0'),('servo0','branch0')],
 'source_disconnected_and_branch0_open':[('source','bus'),('bus','source'),('bus','branch0'),('branch0','bus')],
}
def reachable(start,links):
 seen={start};pending=[start]
 while pending:
  node=pending.pop()
  for a,b in links:
   if a==node and b not in seen:seen.add(b);pending.append(b)
 return 'absorber' in seen
rows=[]
for name,removed in cases.items():
 links=[e for e in edges if e not in removed]
 missing=[f'servo{i}' for i in range(12) if not reachable(f'servo{i}',links)]
 rows.append({'state':name,'removed_edges':removed,'regeneration_sources_without_sink_path':missing,'connectivity_gate':not missing})
report={'scope':plan['question'],'rows':rows,'topology_covers_all_declared_states':all(r['connectivity_gate'] for r in rows),'electrical_protection_verified':False}
(p/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
