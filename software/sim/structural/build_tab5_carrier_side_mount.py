"""Four side-access carrier ears and captive-nut pockets; dimensional prototype only."""
import hashlib,json
from pathlib import Path
import cadquery as cq
ROOT=Path(__file__).resolve().parents[3];out=ROOT/'validation/tab5_carrier_side_mount_v1';out.mkdir(exist_ok=True)
plan={'axes_xz_mm':[[42,z] for z in [88,112]],'sides':[-1,1],'ear_bounds_x_mm':[37,50],'ear_bounds_abs_y_mm':[55,61],'ear_height_mm':8,'clearance_hole_diameter_mm':3.4,'nut_pocket_across_corners_mm':6.6,'nut_pocket_depth_mm':2.8,'basis':'M3 geometry reservation; nut tolerance/grade and screw head/length not selected','criteria':['Both bodies valid connected solids','No new overlap >0.01mm3 with torso components','No overlap between fixed body and carrier'],'stop':'One ear/pocket prototype and static check; no fastening strength acceptance'}
(out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
p=ROOT/'validation/tab5_carrier_v1';files=[p/'carrier.step',p/'fixed_shell.step'];carrier=cq.importers.importStep(str(files[0])).val();fixed=cq.importers.importStep(str(files[1])).val()
for sign in [-1,1]:
 for z in [88,112]:
  ear=cq.Workplane('XY').box(13,6,8).translate((43.5,sign*58,z)).val();carrier=carrier.fuse(ear)
  hole=cq.Solid.makeCylinder(1.7,12,cq.Vector(42,sign*54,z),cq.Vector(0,sign,0));carrier=carrier.cut(hole);fixed=fixed.cut(hole)
  plane=cq.Plane(origin=(42,sign*55,z),xDir=(1,0,0),normal=(0,sign,0))
  pocket=cq.Workplane(plane).polygon(6,6.6).extrude(2.8).val();carrier=carrier.cut(pocket)
carrier=carrier.clean();fixed=fixed.clean()
p=ROOT/'validation/torso_power_integration_v2';files += [p/'report.json',p/'torso_candidate.step'];r=json.loads((p/'report.json').read_text());ss=cq.importers.importStep(str(p/'torso_candidate.step')).val().Solids();assert len(ss)==len(r['parts'])==100
parts={x['name']:s for x,s in zip(r['parts'],ss) if x['name']!='yaw__body_shroud'}
for n,f in {'tray':'validation/lb020_retention_v5/tray.step','battery':'validation/lb020_tray_v1/battery.step','strap_0':'validation/lb020_retention_v5/strap_0.step','strap_1':'validation/lb020_retention_v5/strap_1.step'}.items():
 path=ROOT/f;files.append(path);parts[n]=cq.importers.importStep(str(path)).val()
hits=[]
for n,s in parts.items():
 v=carrier.intersect(s).Volume()
 if v>.01:hits.append({'part':n,'volume_mm3':v})
result={'carrier_valid':carrier.isValid(),'carrier_solids':len(carrier.Solids()),'fixed_valid':fixed.isValid(),'fixed_solids':len(fixed.Solids()),'carrier_fixed_overlap_mm3':carrier.intersect(fixed).Volume(),'other_overlaps':hits,'carrier_volume_mm3':carrier.Volume(),'source_sha256':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},'manufacturing_release':False,'hardware_selected':False,'limits':['No head recess/hardware geometry','No pocket retention during service','No thread strength or preload','Extraction and tool checks must be repeated after hardware selection']}
for n,s in [('carrier',carrier),('fixed_shell',fixed)]:cq.exporters.export(s,str(out/(n+'.step')))
(out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
