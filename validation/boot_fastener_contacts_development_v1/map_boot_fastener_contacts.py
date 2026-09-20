"""Measure nominal fastener bearing faces for subsequent preload/contact analysis."""
import argparse,hashlib,json
from pathlib import Path
import cadquery as cq
from OCP.BRepAdaptor import BRepAdaptor_Surface
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[3]
if a.out.exists():p.error('new output required')
a.out.mkdir(parents=True)
paths=[root/f'validation/boot_low_head_candidate_v1/cad/{s}_boot_shell.step' for s in ('left','right')]+[root/f'validation/native_horn_yoke_development_v1/v4/{s}_foot_yoke.step' for s in ('left','right')]
hardware=root/'validation/captive_boot_hardware_development_v1';paths+=sorted(hardware.glob('*.step'))
plan={'scope':__doc__,'criteria':{'positive_bearing_area_mm2':0,'overlap_max_mm3':.01},'screening_loads_N':[10,20,40],'source_sha256':{str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in paths},'limitations':['Mean force/area only; local contact pressure, bending, creep, thread and pull-through strength remain unverified.','Screening forces are not approved preload or manufacturer requirements.']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
def faces(s,z):
 result=[]
 for f in s.Faces():
  if f.geomType()=='PLANE':
   pl=BRepAdaptor_Surface(f.wrapped).Plane()
   if abs(abs(pl.Axis().Direction().Z())-1)<1e-8 and abs(pl.Location().Z()-z)<1e-6:result.append(f)
 return result
rows=[]
for side in ('left','right'):
 boot=cq.importers.importStep(str(root/f'validation/boot_low_head_candidate_v1/cad/{side}_boot_shell.step')).val()
 yoke=cq.importers.importStep(str(root/f'validation/native_horn_yoke_development_v1/v4/{side}_foot_yoke.step')).val()
 for path in sorted(hardware.glob(f'{side}_*.step')):
  part=cq.importers.importStep(str(path)).val();nut=path.stem.endswith('_nut');z=-14.6 if nut else -19;support=boot if nut else yoke
  area=sum(f.intersect(g).Area() for f in faces(part,z) for g in faces(support,z));overlap=part.intersect(support).Volume()
  rows.append({'hardware':path.name,'support':'boot' if nut else 'yoke','bearing_z_mm':z,'bearing_area_mm2':area,'overlap_mm3':overlap,'mean_pressure_MPa':{str(force):force/area if area>0 else None for force in plan['screening_loads_N']},'nominal_contact_pass':area>0 and overlap<=.01})
report={'rows':rows,'all_nominal_contacts_pass':all(r['nominal_contact_pass'] for r in rows),'preload_qualified':False,'manufacturing_release':False}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'all_nominal_contacts_pass':report['all_nominal_contacts_pass'],'areas_mm2':sorted(set(round(x['bearing_area_mm2'],8) for x in rows))}))
