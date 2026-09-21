"""Conditional screw moment intervals, without assigning uniform collision-envelope density."""
import argparse,csv,hashlib,json,itertools
from pathlib import Path
import numpy as np
import cadquery as cq
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
invpath=Path('board/mechanical/prototype/yaw_support_candidate/revB/inventory.json')
mapath=Path('validation/yaw_hardware_catalog_mass_v1/component_masses.csv')
inv=json.loads(invpath.read_text());byname={x['name']:x for x in inv['parts']}
sources={str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in [invpath,mapath]}
rows=[]
for massrow in csv.DictReader(mapath.open()):
 name=massrow['assembly_part'];part=byname[name];m=float(massrow['nominal_mass_g'])*.001
 if part['source']:
  path=Path(part['source']);h=hashlib.sha256(path.read_bytes()).hexdigest();assert h==part['source_sha256'];sources[str(path)]=h
  shape=cq.importers.importStep(str(path)).val()
  if '_rear_' in name:shape=shape.translate((-.2,0,0))
  b=shape.BoundingBox();lo=np.array([b.xmin,b.ymin,b.zmin])*.001;hi=np.array([b.xmax,b.ymax,b.zmax])*.001
 else:
  # Same nominal plate-screw coordinates as the assembly generator; these are domains, not inertia shapes.
  side,_,idx,_=name.split('_');cy=26 if side=='left' else -26
  x,y=list(itertools.product([-34,8.1],[cy-10,cy+10]))[int(idx)]
  lo=np.array([x-1.9,y-1.9,86.7])*.001;hi=np.array([x+1.9,y+1.9,98])*.001
 sqlo=np.where((lo<=0)&(hi>=0),0,np.minimum(lo**2,hi**2));sqhi=np.maximum(lo**2,hi**2)
 Il=np.zeros((3,3));Ih=Il.copy()
 for i in range(3):
  Il[i,i]=m*(sum(sqlo)-sqlo[i]);Ih[i,i]=m*(sum(sqhi)-sqhi[i])
  for j in range(i):
   vals=[-m*x*y for x in [lo[i],hi[i]] for y in [lo[j],hi[j]]]
   Il[i,j]=Il[j,i]=min(vals);Ih[i,j]=Ih[j,i]=max(vals)
 rows.append({'name':name,'mass_kg':m,'domain_min_m':lo.tolist(),'domain_max_m':hi.tolist(),
 'first_moment_min_kg_m':(m*lo).tolist(),'first_moment_max_kg_m':(m*hi).tolist(),
 'inertia_origin_min_kg_m2':Il.tolist(),'inertia_origin_max_kg_m2':Ih.tolist()})
assert len(rows)==20
keys=['first_moment_min_kg_m','first_moment_max_kg_m','inertia_origin_min_kg_m2','inertia_origin_max_kg_m2']
aggregate={k:sum(np.array(r[k]) for r in rows).tolist() for k in keys}
aggregate['mass_kg']=sum(r['mass_kg'] for r in rows)
assert abs(aggregate['mass_kg']-.01236)<1e-12
out={'source_sha256':sources,'parts':rows,'aggregate':aggregate,
 'interpretation':'Componentwise outer bounds for arbitrary nonnegative mass distribution contained in each declared box at catalog nominal mass. Endpoint tensor entries are not necessarily jointly realizable.',
 'limitations':['Nominal CAD domains are not proven manufactured containment envelopes; screw head and length tolerances need expansion.',
 'Catalog mass has no guaranteed tolerance here.', 'No point estimate of screw COM or inertia assigned.', 'No MuJoCo inertia updated.'],
 'physical_bounds_qualified':False,'manufacturing_release':False}
a.out.mkdir(parents=True,exist_ok=False);(a.out/'report.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(aggregate))
