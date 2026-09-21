"""Generate one bounded rear-mounted rail-bracket candidate and screen fit."""
import argparse,hashlib,json
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();paths=[]
def read(p):
 p=Path(p);paths.append(p);return json.loads(p.read_text())
def box(x0,x1,y0,y1,z0,z1):return cq.Solid.makeBox(x1-x0,y1-y0,z1-z0,cq.Vector(x0,y0,z0))
plan=read(a.out/'plan.json');d=plan['assumptions'];placement=read('validation/dual_pololu_mounted_layout_v1/report.json')['placements']
root=Path('validation/yaw_integrated_candidate_v7');items=read(root/'inventory.json')['parts'];sp=root/'yaw_support_candidate.step';paths.append(sp)
ss=cq.importers.importStep(str(sp)).val().Solids();assert len(ss)==len(items)==52
targets={i['name']:s for i,s in zip(items,ss)}
for n,f in {'tray':'board/mechanical/prototype/rc_battery_tray_revB/tray.step','battery':'validation/rc_battery_cad_v1_checked/battery_candidate.step','Tab5':'software/sim/mujoco/assets/r9_fast_turn_v1/cad/Tab5.step','TTL':'software/sim/mujoco/assets/r9_fast_turn_v1/cad/TTL_interface.step'}.items():
 paths.append(Path(f));targets[n]=cq.importers.importStep(f).val()
parts={};holes={};rows=[]
for place in placement:
 side=place['side'];pts=place['mount_axes_mm'];ys=sorted({v[1] for v in pts});zs=[108.,115.];ym=sum(ys)/2;y0,y1=ys[0]-2,ys[1]+2;z0,z1=d['rail_bottom_z_mm'],d['rail_top_z_mm']
 s=box(-62.2,-58.2,y0,y1,z0,d['rear_flange_top_z_mm'])
 for y in ys:s=s.fuse(box(-58.2,-3.569,y-2,y+2,z0,z1))
 s=s.fuse(box(-7.569,-3.569,y0,y1,z0,z1))
 for x,y,z in pts:s=s.cut(cq.Solid.makeCylinder(1.1,20,cq.Vector(x,y,90)))
 for z in zs:s=s.cut(cq.Solid.makeCylinder(1.7,10,cq.Vector(-65,ym,z),cq.Vector(1,0,0)))
 s=s.clean();assert len(s.Solids())==1 and s.isValid();parts[side]=s;holes[side]=[[ym,z] for z in zs];cq.exporters.export(s,str(a.out/(side+'_bracket.step')))
 for name,t in targets.items():
  row={'bracket':side,'part':name,'overlap_mm3':s.intersect(t).Volume(),'distance_mm':s.distance(t),'intended_contact':name=='rear_plate'}
  if name=='rear_plate':
   row['contact_area_mm2']=None
   row['contact_position_matches']=row['distance_mm']<1e-7
  rows.append(row)
rows.append({'bracket':'left','part':'right_bracket','overlap_mm3':parts['left'].intersect(parts['right']).Volume(),'distance_mm':parts['left'].distance(parts['right']),'intended_contact':False})
bad=[r for r in rows if r['overlap_mm3']>plan['criteria']['maximum_unintended_overlap_mm3'] or (r['intended_contact'] and not r.get('contact_position_matches',False)) or (not r['intended_contact'] and r['distance_mm']<plan['criteria']['minimum_unintended_clearance_mm'])]
r={'checks':rows,'failed_checks':bad,'nominal_fit_pass':not bad,'rear_plate_proposed_holes_yz_mm':holes,'bracket_volume_mm3':{n:s.Volume() for n,s in parts.items()},'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},'manufacturing_release':False}
(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'failures':bad,'volumes':r['bracket_volume_mm3']},indent=2))
