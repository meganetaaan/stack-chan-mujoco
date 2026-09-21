from pathlib import Path
import json,numpy as np
p=Path(__file__).resolve().parent
arr=np.load(p/'constraints.npz');lines=(p/'contact.inp').read_text().splitlines();equations=[];i=0
while i<len(lines):
 if lines[i]=='*EQUATION':
  n=int(lines[i+1]);i+=2;terms=[]
  while len(terms)<n:
   values=lines[i].split(',');assert len(values)%3==0 and len(values)<=12
   terms.extend((int(values[k]),int(values[k+1]),float(values[k+2])) for k in range(0,len(values),3));i+=1
  assert len(terms)==n;equations.append(terms)
 else:i+=1
k=0;errors=[]
for name in ['BOSS','SPACER']:
 ids=arr[name+'_node_ids'];lookup={int(n):i for i,n in enumerate(ids)};D=arr[name+'_reduced_matrix']
 for row in D:
  actual=np.zeros_like(row)
  for n,d,v in equations[k]:actual[3*lookup[n]+d-1]=v
  errors.append(float(np.max(abs(actual-row))/max(np.max(abs(row)),1)));k+=1
assert k==len(equations)==9
result={'maximum_normalized_coefficient_error':max(errors),'limit':1e-11,'passed':max(errors)<=1e-11,'solver_completed':False}
(p/'serialization_check.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
