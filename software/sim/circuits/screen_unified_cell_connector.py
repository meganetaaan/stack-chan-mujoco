"""Enumerate connector opens/miswiring: source potentials, not IC simulation."""
import itertools,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
out=ROOT/'validation/unified_cell_connector_v1'
out.mkdir(exist_ok=True)
# Each logical board port has exactly one battery source. No duplicate return.
ports=('B0','B1','B2','B3')
cases=[]
for mapping in itertools.permutations(range(4)):
 for mask in range(16):
  connected={p:mapping[i] for i,p in enumerate(ports) if mask & (1<<i)}
  relative={p:(source-connected['B0']) for p,source in connected.items()} if 'B0' in connected else None
  cases.append({'mapping':mapping,'connected_mask':mask,'source_cell_units_relative_B0':relative,
   'negative_source_relative_VSS': None if relative is None else any(v<0 for v in relative.values()),
   'VSS_reference_missing':'B0' not in connected,
   'safe_fault_proven':False})
reverse=next(c for c in cases if c['mapping']==(3,1,2,0) and c['connected_mask']==15)
assert reverse['source_cell_units_relative_B0']=={'B0':0,'B1':-2,'B2':-1,'B3':-3}
assert len(cases)==384
report={'scope':'Independent ideal source assignments at connector; no clamps, filters, leakage, contact bounce or partial contact resistance modeled',
 'proposal':'One four-pole robot interface. Adapter uses XT30 B0/B3 and balance B1/B2 ONLY. Balance end leads individually insulated and not joined.',
 'physical_pin_number_mapping':None,'cases':cases,
 'main_reversal_counterexample':reverse,
 'decision':'No duplicate-return wire short in this topology, but reversed main creates negative sense source voltages. Do not integrate as reverse-protected design.',
 'manufacturing_release':False}
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print('384 source-assignment/open-contact cases; main reversal gives B1=-2, B2=-1 cell units relative VSS; not qualified')
