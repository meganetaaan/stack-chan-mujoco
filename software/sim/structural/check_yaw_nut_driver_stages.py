"""Axially swept selected nut-driver envelope in full and detached-side assemblies."""
import argparse,hashlib,json
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
base=Path('validation/yaw_integrated_candidate_v6');ip=base/'inventory.json';sp=base/'yaw_support_candidate.step';specpath=Path('docs/prototype/mechanical/yaw_nut_driver/candidate.json');spec=json.loads(specpath.read_text());items=json.loads(ip.read_text())['parts'];solids=cq.importers.importStep(str(sp)).val().Solids();assert len(items)==len(solids)==52
parts={};files=[ip,sp,specpath]
for item,s in zip(items,solids):
 assert abs(item['volume_mm3']-s.Volume())<1e-5
 name=item['name']
 if name in ['left_yaw_fixed_support','right_yaw_fixed_support']:
  f=Path('validation/yaw_upper_tool_relief_v1')/(name+'.step');files.append(f);s=cq.importers.importStep(str(f)).val()
 parts[name]=s
z0=91.9;travel=max(s.BoundingBox().zmax for s in parts.values())+5-z0;assert travel>0
plan={'question':'Can the selected tool approach axially after assembly, or while one support/plate is detached?', 'criterion_nominal_clearance_mm':.9,'tool':'Catalog blade and handle cylinders, each swept continuously upwards; not a detailed purchased solid.', 'insertion_travel_mm':travel,'stages':['all52parts','same-side support, plate and all four complete plate fasteners only'],'intentional_exclusions':'Target screw and target nut excluded because socket cavity not specified; engagement and bottoming remain unverified. Washer remains included.', 'stop':'Eight axes, two stages; no geometry or clearance changes.', 'limits':['No hand, lower reaction tool, harness, Tab5 or battery beyond fixed assembly.','0.9 mm is existing engineering budget, not manufacturer tolerance.','Detached stage does not prove later support installation.']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');rows=[]
for name,nut in parts.items():
 if '_plate_' not in name or not name.endswith('_nut'):continue
 key=name[:-4];side=name.split('_')[0];b=nut.BoundingBox();x=(b.xmin+b.xmax)/2;y=(b.ymin+b.ymax)/2
 shaft=cq.Solid.makeCylinder(spec['blade_diameter_catalog_mm']/2,spec['blade_length_mm']+travel,cq.Vector(x,y,z0))
 handle=cq.Solid.makeCylinder(max(spec['overall_catalog_dimensions_mm'][1:])/2,spec['handle_length_mm']+travel,cq.Vector(x,y,z0+spec['blade_length_mm']))
 tool=cq.Compound.makeCompound([shaft,handle]);exclude={key+'_nut',key+'_screw'}
 for stage in ['all52parts','detached_side']:
  selected={n:s for n,s in parts.items() if n not in exclude and (stage=='all52parts' or n in [side+'_yaw_fixed_support',side+'_mount_plate'] or n.startswith(side+'_plate_'))}
  checks=[]
  for n,s in selected.items():
   d=tool.distance(s);checks.append({'part':n,'distance_mm':d,'pass':d>=.9-1e-8})
  rows.append({'nut':name,'stage':stage,'checked_parts':len(checks),'minimum_clearance_mm':min(c['distance_mm'] for c in checks),'failures':[c for c in checks if not c['pass']]})
r={'rows':rows,'source_sha256':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},'stage_pass':{stage:all(not r['failures'] for r in rows if r['stage']==stage) for stage in ['all52parts','detached_side']},'assembly_verified':False,'manufacturing_release':False}
(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'stage_pass':r['stage_pass'],'failures':[{'nut':x['nut'],'stage':x['stage'],'failures':x['failures']} for x in rows if x['failures']]},indent=2))
