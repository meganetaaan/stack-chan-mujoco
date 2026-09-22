"""Directed connectivity through ideal FET channels and body diodes."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[3]
d=json.loads((ROOT/'schematics/power/bq76942_pack_fet_candidate.json').read_text())
rows=[]
for chg in [False,True]:
 for dsg in [False,True]:
  edges=[]
  for ref,on in [('Q_CHG',chg),('Q_DSG',dsg)]:
   pins=d['pin_connections'][ref]
   assert len({pins[str(i)] for i in [1,2,3]})==1
   assert len({pins[str(i)] for i in [5,6,7,8]})==1
   s,t=pins['1'],pins['5']
   edges.append((s,t)) # NMOS intrinsic diode
   if on:edges.append((t,s))
  def reachable(start,end):
   seen={start}
   for _ in range(len(edges)):
    seen |= {b for a,b in edges if a in seen}
   return end in seen
  rows.append({'CHG_ON':chg,'DSG_ON':dsg,'discharge_path_exists':reachable('CELL_POS_FUSED','PACK_POS_PROTECTED'),'charge_path_exists':reachable('PACK_POS_PROTECTED','CELL_POS_FUSED')})
out=ROOT/'validation/bq76942_pack_fet_pinmap_v1/report.json'
out.write_text(json.dumps({'scope':'ideal graph; excludes leakage, breakdown, parasitic paths and actual gate states','states':rows,'manufacturing_release':False},indent=2)+'\n')
print(rows)
