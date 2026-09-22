"""Integrate removable face carrier and protected battery packaging candidates."""
import hashlib,json,itertools
from pathlib import Path
import cadquery as cq
ROOT=Path(__file__).resolve().parents[3];out=ROOT/'validation/serviceable_torso_v1';out.mkdir(exist_ok=True)
plan={'scope':'Static integration of current carrier hardware and LB-020 route candidates','criteria':'Flag all new-vs-retained and new-vs-new volume overlaps above0.01mm3','stop':'One integration audit; expected threaded screw/nut contact must be reviewed explicitly','limits':['Tab5-to-carrier screws absent','No new protection PCB/cables','No articulated legs or tolerance/strength acceptance']}
(out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
p=ROOT/'validation/torso_power_integration_v2';r=json.loads((p/'report.json').read_text());ss=cq.importers.importStep(str(p/'torso_candidate.step')).val().Solids();assert len(ss)==len(r['parts'])==100
parts={x['name']:s for x,s in zip(r['parts'],ss) if x['name'] not in ('yaw__body_shroud','tray','battery')};old_names=set(parts);files=[p/'report.json',p/'torso_candidate.step']
paths={'new_fixed_shell':'validation/tab5_carrier_hardware_v2/fixed_shell.step','new_carrier':'validation/tab5_carrier_hardware_v2/carrier.step','new_tray':'validation/lb020_retention_v5/tray.step','new_battery':'validation/lb020_tray_v1/battery.step',**{f'new_strap_{i}':f'validation/lb020_retention_v5/strap_{i}.step' for i in range(2)}}
for sign in [-1,1]:
 for z in [88,112]:
  for kind in ['screw','nut']:paths[f'new_{sign}_{z}_{kind}']=f'validation/tab5_carrier_hardware_v2/{sign}_{z}_{kind}.step'
for n,f in paths.items():
 path=ROOT/f;files.append(path);parts[n]=cq.importers.importStep(str(path)).val()
assert len(parts)==111
hits=[];tested=0;pruned=0
for (n,s),(m,t) in itertools.combinations(parts.items(),2):
 if n in old_names and m in old_names:continue
 tested+=1;a,b=s.BoundingBox(),t.BoundingBox()
 if any(getattr(a,k+'max')<=getattr(b,k+'min') or getattr(b,k+'max')<=getattr(a,k+'min') for k in 'xyz'):pruned+=1;continue
 v=s.intersect(t).Volume()
 if v>.01:hits.append({'parts':[n,m],'overlap_mm3':v})
assembly=cq.Compound.makeCompound(list(parts.values()));bb=assembly.BoundingBox();cq.exporters.export(assembly,str(out/'assembly.step'))
result={'part_count':len(parts),'pairs_checked':tested,'bounding_box_pruned':pruned,'overlap_flags':hits,'bbox_mm':{k:[getattr(bb,k+'min'),getattr(bb,k+'max')] for k in 'xyz'},'parts':[{'name':n,'volume_mm3':s.Volume()} for n,s in parts.items()],'source_sha256':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},'manufacturing_release':False,'whole_robot_verified':False}
(out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('parts','source_sha256')}))
