"""Split front shroud into a removable carrier; fastening not yet qualified."""
import hashlib,json
from pathlib import Path
import cadquery as cq
ROOT=Path(__file__).resolve().parents[3];out=ROOT/'validation/tab5_carrier_v1';out.mkdir(exist_ok=True)
plan={'split_plane_x_mm':46,'seam_mm':.3,'pad_radius_mm':3.5,'pad_x_mm':[48,52],'mount_clearance_radius_mm':1.65,'axes_yz_mm':[[y,z] for y in [-60,60] for z in [52,124]],'criteria':['Connected valid fixed shell and carrier','No new volume overlaps >0.01mm3','No growth of torso bounds'],'basis':'Split plane, seam, pad and clearance sizes are engineering candidates; not qualified manufacturing tolerances','stop':'One partition/nominal interference and forward group swept-box screen. No strength claim before carrier-to-body fastening.'}
(out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
p=ROOT/'validation/torso_power_integration_v2';r=json.loads((p/'report.json').read_text());ss=cq.importers.importStep(str(p/'torso_candidate.step')).val().Solids();assert len(ss)==len(r['parts'])==100
parts=dict(zip([x['name'] for x in r['parts']],ss));shell=parts.pop('yaw__body_shroud')
def box(d,c):return cq.Workplane('XY').box(*d).translate(tuple(c)).val()
fixed=shell.intersect(box([300,300,300],[-104,0,64])).clean()
carrier=shell.intersect(box([100,300,300],[96.3,0,64]))
for y,z in plan['axes_yz_mm']:
 carrier=carrier.fuse(cq.Solid.makeCylinder(3.5,4,cq.Vector(48,y,z),cq.Vector(1,0,0)))
 carrier=carrier.cut(cq.Solid.makeCylinder(1.65,10,cq.Vector(44,y,z),cq.Vector(1,0,0)))
carrier=carrier.clean();files=[p/'report.json',p/'torso_candidate.step']
for n,f in {'tray':'validation/lb020_retention_v5/tray.step','battery':'validation/lb020_tray_v1/battery.step','strap_0':'validation/lb020_retention_v5/strap_0.step','strap_1':'validation/lb020_retention_v5/strap_1.step'}.items():
 path=ROOT/f;files.append(path);parts[n]=cq.importers.importStep(str(path)).val()
rows=[]
for n,s in parts.items():
 v=carrier.intersect(s).Volume()
 if v>.01:rows.append({'part':n,'overlap_mm3':v})
old=cq.Compound.makeCompound([shell,*parts.values()]).BoundingBox();new=cq.Compound.makeCompound([fixed,carrier,*parts.values()]).BoundingBox()
within=all(getattr(new,k+'min')>=getattr(old,k+'min')-1e-6 and getattr(new,k+'max')<=getattr(old,k+'max')+1e-6 for k in 'xyz')
group=cq.Compound.makeCompound([carrier,parts['Tab5']]);bb=group.BoundingBox();travel=69-bb.xmin
sweep=box([bb.xlen+travel,bb.ylen,bb.zlen],[(bb.xmin+bb.xmax+travel)/2,(bb.ymin+bb.ymax)/2,(bb.zmin+bb.zmax)/2])
service_hits=[]
for n,t in {'fixed_shell':fixed,**{n:t for n,t in parts.items() if n!='Tab5'}}.items():
 v=sweep.intersect(t).Volume()
 if v>.01:service_hits.append({'part':n,'overlap_mm3':v})
projection_checks=[]
for hit in service_hits:
 n=hit['part'];t=parts[n];tb=t.BoundingBox()
 prism=box([400,tb.ylen,tb.zlen],[0,(tb.ymin+tb.ymax)/2,(tb.zmin+tb.zmax)/2])
 v=carrier.intersect(prism).Volume()
 tab_forward_separated=parts['Tab5'].BoundingBox().xmin>=tb.xmax
 projection_checks.append({'part':n,'carrier_intersection_with_YZ_prism_mm3':v,'Tab5_stays_forward_of_part':tab_forward_separated,'false_positive_resolved':v<1e-8 and tab_forward_separated})
result={'sweep_box_flag_resolution':projection_checks,'group_removal_travel_mm':travel,'group_removal_box_flags':service_hits,'carrier_valid':carrier.isValid(),'carrier_solids':len(carrier.Solids()),'fixed_valid':fixed.isValid(),'fixed_solids':len(fixed.Solids()),'carrier_volume_mm3':carrier.Volume(),'fixed_volume_mm3':fixed.Volume(),'carrier_fixed_overlap_mm3':carrier.intersect(fixed).Volume(),'carrier_fixed_gap_mm':carrier.distance(fixed),'other_overlaps':rows,'torso_bounds_preserved':within,'source_sha256':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},'manufacturing_release':False,'carrier_fasteners_defined':False}
for n,s in [('fixed_shell',fixed),('carrier',carrier)]:cq.exporters.export(s,str(out/(n+'.step')))
(out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
