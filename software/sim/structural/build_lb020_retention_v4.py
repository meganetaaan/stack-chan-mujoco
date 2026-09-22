"""ONE-WRAP 31013 width and conservative doubled closure envelope; not qualified."""
import hashlib,json
from pathlib import Path
import cadquery as cq
ROOT=Path(__file__).resolve().parents[3];out=ROOT/'validation/lb020_retention_v4';out.mkdir(exist_ok=True)
plan={'strap_centers_y_mm':[-12,12],'strap_width_mm':12.7,'strap_thickness_envelope_mm':2.5,'closure_layers':2,'closure_region_z_min_mm':80,'guide_clear_width_mm':13.7,'candidate_part':'VELCRO 31013','cut_length_mm':200,'basis':'Manufacturer width12.7mm;2.5mm single-layer thickness is an unverified design allowance. Place and constrain closure on upper U route z>=80mm.2.5mm thickness allowance unchanged; this is a different specified assembly, not a relaxation of v2.','criteria':['Valid single tray solid','No volume overlap with battery or straps','No new volume overlap with98 torso parts'],'threshold_mm3':.01,'stop':'One two-strap route; do not perform FE or claim retention before selecting closure and load/pressure limits'}
(out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
def box(d,c):return cq.Workplane('XY').box(*d).translate(tuple(c)).val()
source=ROOT/'validation/lb020_tray_v1/tray.step';tray=cq.importers.importStep(str(source)).val();battery=cq.importers.importStep(str(source.with_name('battery.step'))).val()
straps=[]
for y in plan['strap_centers_y_mm']:
 single=box([33.4,12.7,42.5],[29,y,79.25]).cut(box([28.4,15,37.5],[29,y,79.25]))
 double=box([38.4,12.7,47.5],[29,y,79.25]).cut(box([28.4,15,37.5],[29,y,79.25]))
 upper=double.intersect(box([50,15,30],[29,y,95]))
 straps.append(single.fuse(upper).clean())
 for gy in [y-7.6,y+7.6]:
  for x in [14.25,43.75]:tray=tray.fuse(box([1.5,1.5,9.5],[x,gy,65.25]))
tray=tray.clean()
p=ROOT/'validation/torso_power_integration_v2';r=json.loads((p/'report.json').read_text());ss=cq.importers.importStep(str(p/'torso_candidate.step')).val().Solids();assert len(ss)==len(r['parts'])==100
parts=dict(zip([x['name'] for x in r['parts']],ss));checks=[]
objects={'tray':tray,**{f'strap_{i}':s for i,s in enumerate(straps)}}
for n,s in objects.items():
 for m,t in parts.items():
  if m in ['tray','battery']:continue
  v=s.intersect(t).Volume()
  if v>.01:checks.append({'candidate':n,'part':m,'volume_mm3':v})
internal={'tray_battery':tray.intersect(battery).Volume(),**{f'tray_strap_{i}':tray.intersect(s).Volume() for i,s in enumerate(straps)},**{f'battery_strap_{i}':battery.intersect(s).Volume() for i,s in enumerate(straps)}}
for n,s in objects.items():cq.exporters.export(s,str(out/(n+'.step')))
result={'valid_tray':tray.isValid(),'tray_solids':len(tray.Solids()),'volume_mm3':tray.Volume(),'internal_overlaps_mm3':internal,'external_overlaps':checks,'minimum_external_gap_mm':{n:min(s.distance(t) for m,t in parts.items() if m not in ('tray','battery')) for n,s in objects.items()},'source_sha256':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [source,source.with_name('battery.step'),p/'report.json',p/'torso_candidate.step']},'strap_spacing_mm':24,'previous_spacing_mm':40,'pure_couple_force_multiplier':40/24,'manufacturing_release':False,'limits':['Upper U double-layer reservation; assembly must retain closure at z>=80mm; bend radius and installation unqualified','Published closure values are typical, not design allowables; pressure limit unknown','No tolerance, flexure or strength qualification']}
(out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
