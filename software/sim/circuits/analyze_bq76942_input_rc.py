"""Linear coupled-RC response; no battery dynamics or protector timing model."""
import json
from pathlib import Path
import numpy as np
from scipy.linalg import expm
ROOT=Path(__file__).resolve().parents[3]
a=json.loads((ROOT/'schematics/power/bq76942_candidate.json').read_text())
b=json.loads((ROOT/'schematics/power/bq76942_series_filter_candidate.json').read_text())
nodes=[x['resistor'][1] for x in a['cell_input_filter_candidate']['branches']]
index={n:i for i,n in enumerate(nodes)}
r=a['cell_input_filter_candidate']['resistor']
R=r['resistance_ohm']*(1+r['initial_tolerance_fraction'])
G=np.eye(4)/R
D=np.diff(np.eye(4),axis=0)
# One physical cell step moves all taps above that cell, at constant B-.
steps=[np.array([0]+[float(j>=k) for j in range(1,4)]) for k in range(1,4)]
rows=[]
for fault_index in [None]+list(range(4)):
 for fault in (['none'] if fault_index is None else ['open','short']):
  C=np.zeros((4,4))
  values=[]
  for i,f in enumerate(b['filters']):
   assert len(f['capacitors'])==6
   # Parallel-bank reduction, identical maximum-initial-tolerance capacitors.
   counts=[3,3]
   if i==fault_index and fault=='open':counts[0]=2
   cap=100e-9*1.05*(3 if i==fault_index and fault=='short' else counts[0]*counts[1]/sum(counts))
   values.append(cap)
   v=np.zeros(4)
   for sign,n in zip([1,-1],f['terminals']):
    if n in index:v[index[n]]+=sign
    else:assert n=='CELL_B_MINUS'
   C+=cap*np.outer(v,v)
  A=-np.linalg.solve(C,G)
  tau=max(-1/np.linalg.eigvals(A)).real
  response=[]
  for k,s in enumerate(steps,1):
   for t in [10e-6,50e-6,100e-6]:
    y=D@((np.eye(4)-expm(A*t))@s)
    response.append({'physical_cell_step':k,'time_s':t,'differential_response_per_unit_step':y.tolist()})
  rows.append({'fault':fault,'filter':fault_index,'capacities_F':values,'largest_mode_time_constant_s':float(tau),'responses':response})
out=ROOT/'validation/bq76942_input_rc_v1';out.mkdir(exist_ok=True)
report={'scope':'linear passive RC only; all initial R,C at upper limits; not all tolerance corners or IC delay','resistance_ohm':R,'cases':rows,'qualification':False}
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print([(x['fault'],x['filter'],round(x['largest_mode_time_constant_s']*1e6,4)) for x in rows])
