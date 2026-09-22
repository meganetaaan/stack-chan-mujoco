"""LB-020 horizontal tray proposal, fixed battery center and mounting axes."""
import hashlib,json
from pathlib import Path
import cadquery as cq
ROOT=Path(__file__).resolve().parents[3];out=ROOT/'validation/lb020_tray_v1';out.mkdir(exist_ok=True)
plan={'battery_xyz_mm':[24,70,36],'center_mm':[29,0,80],'side_clearance_mm':.7,'clearance_basis':'engineering assumption, not qualified swelling/tolerance allowance','wall_floor_mm':1.5,'wall_height_mm':8,'overlap_flag_mm3':.01,'criteria':['One valid connected tray solid','No battery volume intersection','No new volume intersection with other98 torso parts','Torso axis-aligned bounds not enlarged'],'stop':'One geometry and static screen; preserve failed criteria; no FE before retention and load path defined'}
(out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
def box(d,c):return cq.Workplane('XY').box(*d).translate(tuple(c)).val()
blocks=[([28.4,74.4,1.5],[29,0,61.25])]
for sign in [-1,1]:
 blocks += [([1.5,74.4,8],[29+sign*13.45,0,66]),([28.4,1.5,8],[29,sign*36.45,66]),([6,26,3],[29,sign*49,60.05]),([6,2,8],[29,sign*61.2,62]),([6,8,5.2],[29,sign*36,62])]
tray=box(*blocks[0])
for d,c in blocks[1:]:tray=tray.fuse(box(d,c))
# Clear the battery cavity through any original connecting arms.
tray=tray.cut(box([25.4,71.4,60],[29,0,92]))
for sign in [-1,1]:tray=tray.cut(cq.Solid.makeCylinder(1.1,4,cq.Vector(29,sign*59.2,63),cq.Vector(0,sign,0)))
tray=tray.clean();battery=box(plan['battery_xyz_mm'],plan['center_mm'])
p=ROOT/'validation/torso_power_integration_v2';r=json.loads((p/'report.json').read_text());ss=cq.importers.importStep(str(p/'torso_candidate.step')).val().Solids();assert len(ss)==len(r['parts'])==100
parts=dict(zip([x['name'] for x in r['parts']],ss));old=cq.Compound.makeCompound(ss).BoundingBox()
rows=[]
for n,s in parts.items():
 if n in ('tray','battery'):continue
 v=tray.intersect(s).Volume()
 if v>.01:rows.append({'part':n,'overlap_mm3':v})
new=cq.Compound.makeCompound([s for n,s in parts.items() if n not in ('tray','battery')]+[tray,battery]).BoundingBox()
bounds=lambda b:{k:[getattr(b,k+'min'),getattr(b,k+'max')] for k in 'xyz'}
within=all(getattr(new,k+'min')>=getattr(old,k+'min')-1e-6 and getattr(new,k+'max')<=getattr(old,k+'max')+1e-6 for k in 'xyz')
result={'valid':tray.isValid(),'solid_count':len(tray.Solids()),'volume_mm3':tray.Volume(),'battery_overlap_mm3':tray.intersect(battery).Volume(),'other_part_overlaps':rows,'old_torso_bounds_mm':bounds(old),'new_torso_bounds_mm':bounds(new),'torso_bounds_preserved':within,'mount_axes_mm':[[29,-61.2,63],[29,61.2,63]],'source_sha256':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [p/'report.json',p/'torso_candidate.step']},'manufacturing_release':False,'retention_strength_verified':False}
for name,s in [('tray',tray),('battery',battery)]:cq.exporters.export(s,str(out/(name+'.step')))
(out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
