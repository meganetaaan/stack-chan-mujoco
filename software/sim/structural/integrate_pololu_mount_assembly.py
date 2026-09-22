"""Unify latest mount hardware with explicit geometry-to-BOM identities."""
import argparse,json,hashlib,csv,math
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();paths=[]
def read(p):
 p=Path(p);paths.append(p);return json.loads(p.read_text())
def load(p):
 p=Path(p);paths.append(p);return cq.importers.importStep(str(p)).val()
def bounds(s):
 b=s.BoundingBox();return [getattr(b,k) for k in ['xmin','xmax','ymin','ymax','zmin','zmax']]
plan=read(a.out/'plan.json');spec=read('docs/prototype/mechanical/pololu_mount_fasteners/candidate.json');rear=read('docs/prototype/mechanical/pololu_mount_fasteners/rear_candidate.json');places=read('validation/dual_pololu_mounted_layout_v1/report.json')['placements'];rd=Path('validation/pololu_rear_fasteners_v1')
parts={};meta={}
def add(n,s,part,group):
 assert n not in parts and s.isValid() and len(s.Solids())==1
 parts[n]=s;meta[n]={'part_number':part,'group':group,'volume_mm3':s.Volume(),'bounds_mm':bounds(s)}
for n,file in [('rear_plate','rear_plate.step'),('left_bracket','left_bracket.step'),('right_bracket','right_bracket.step')]:add(n,load(rd/file),'custom '+n,'structure')
# Identify solids geometrically, not merely by import order.
rss=load(rd/'rear_joint.step').Solids();assert len(rss)==19
for s in rss:
 b=s.BoundingBox()
 if s.Volume()>1000:continue
 side='left' if b.ymin>0 else 'right';z=(b.zmin+b.zmax)/2;assert min(abs(z-107),abs(z-115))<1e-5;i=0 if abs(z-107)<1e-5 else 1
 if abs(b.xmin+66.7)<1e-5:kind='screw';key='screw'
 elif abs(b.xmin+64.7)<1e-5:kind='outer_washer';key='washer'
 elif abs(b.xmin+58.2)<1e-5:kind='inner_washer';key='washer'
 elif abs(b.xmin+57.7)<1e-5:kind='nut';key='nut'
 else:raise AssertionError(bounds(s))
 add(f'{side}_rear_{i}_{kind}',s,rear[key]['part'],'rear_hardware')
assert len(parts)==19
for place in places:
 side=place['side'];ss=load(Path('validation/pololu_captive_nut_v1')/(side+'_with_fasteners.step')).Solids();assert len(ss)==9
 for s in ss:
  if s.Volume()>1000:continue
  b=s.BoundingBox();x,y=(b.xmin+b.xmax)/2,(b.ymin+b.ymax)/2
  idx=[i for i,v in enumerate(place['mount_axes_mm']) if abs(v[0]-x)<1e-5 and abs(v[1]-y)<1e-5];assert len(idx)==1
  if abs(b.zmax-96.9)<1e-5:kind='nut';pn='Bossard '+spec['nut']['article']
  else:assert abs(b.zmin-94.6398)<1e-5;kind='screw';pn='NBK '+spec['screw']['part']
  add(f'{side}_module_{idx[0]}_{kind}',s,pn,'module_hardware')
 for i,(x,y,z) in enumerate(place['mount_axes_mm']):
  sp=spec['spacer'];bottom=z-sp['length_mm'];s=cq.Solid.makeCylinder(sp['outer_diameter_mm']/2,sp['length_mm'],cq.Vector(x,y,bottom)).cut(cq.Solid.makeCylinder(sp['inner_diameter_mm']/2,sp['length_mm'],cq.Vector(x,y,bottom)))
  add(f'{side}_module_{i}_spacer',s,'MISUMI '+sp['part'],'spacer')
assert len(parts)==43
rows=[]
def check(n,m,intended=False):
 s,t=parts[n],parts[m];rows.append({'part':n,'obstacle':m,'intended_contact_or_bore':intended,'overlap_mm3':s.intersect(t).Volume(),'distance_mm':s.distance(t)})
module=[n for n in parts if meta[n]['group']=='module_hardware'];rear_names=[n for n in parts if meta[n]['group']=='rear_hardware'];spacers=[n for n in parts if meta[n]['group']=='spacer']
for n in module:
 for m in rear_names:check(n,m)
 for m in ['rear_plate','left_bracket','right_bracket']:check(n,m,m.startswith(n.split('_')[0]) and m.endswith('bracket'))
for n in spacers:
 for m in rear_names+module+['rear_plate','left_bracket','right_bracket']:
  ownshaft=m==n.replace('_spacer','_screw');ownbracket=m==n.split('_')[0]+'_bracket';check(n,m,ownshaft or ownbracket)
bad=[r for r in rows if r['overlap_mm3']>plan['criteria']['maximum_overlap_mm3'] or (not r['intended_contact_or_bore'] and r['distance_mm']<plan['criteria']['minimum_unintended_clearance_mm'])]
assembly=cq.Compound.makeCompound(list(parts.values()));cq.exporters.export(assembly,str(a.out/'mount_assembly.step'))
inv={'parts':[{'name':n,**meta[n]} for n in parts],'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},'manufacturing_release':False};(a.out/'inventory.json').write_text(json.dumps(inv,indent=2)+'\n')
bom={}
for n in parts:
 pn=meta[n]['part_number'];bom[pn]=bom.get(pn,0)+1
with (a.out/'bom.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['part','quantity','status']);w.writerows((pn,q,'comparison only') for pn,q in bom.items())
r={'part_count':len(parts),'checks':rows,'failed_checks':bad,'nominal_integration_pass':not bad,'minimum_unintended_gap_mm':min(r['distance_mm'] for r in rows if not r['intended_contact_or_bore']),'manufacturing_release':False};(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:r[k] for k in ['part_count','failed_checks','nominal_integration_pass','minimum_unintended_gap_mm']},indent=2))
