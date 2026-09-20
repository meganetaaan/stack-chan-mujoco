"""Compare the structural solver with a slender cantilever's analytical deflection."""
import argparse,json
from pathlib import Path
import cadquery as cq
import numpy as np
from elasticity import tetrahedralize, analyze

p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
a.out.mkdir(parents=True,exist_ok=False)
shape=cq.Workplane('XY').box(40,10,4,centered=(False,True,True)).val()
cq.exporters.export(shape,str(a.out/'beam.step'))
rows=[]
for h in [4.,3.,2.]:
 m=tetrahedralize(a.out/'beam.step',a.out/f'beam_{h}.msh',h)
 r,d=analyze(m,lambda x:abs(x[0])<1e-7,lambda x:abs(x[0]-40)<1e-7,[40,0,0],[0,0,1,0,0,0])
 expected=40**3/(3*1400*(10*4**3/12))
 r.update(mesh_mm=h,euler_bernoulli_mm=expected,relative_error=(r['max_displacement_mm']/expected-1))
 rows.append(r);print(json.dumps(r),flush=True)
 np.savez_compressed(a.out/f'beam_{h}.npz',**d)
report={'scope':__doc__,'rows':rows,'passed':abs(rows[-1]['relative_error'])<.03 and abs(rows[-1]['max_displacement_mm']/rows[-2]['max_displacement_mm']-1)<.02}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
raise SystemExit(0 if report['passed'] else 1)
