"""Integrate selected rear fastening stack and shifted lower mounting holes."""
import argparse,json,hashlib,math,itertools
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();paths=[]
def read(p):
 p=Path(p);paths.append(p);return json.loads(p.read_text())
def cyl(r,l,x,y,z):return cq.Solid.makeCylinder(r,l,cq.Vector(x,y,z),cq.Vector(1,0,0))
plan=read(a.out/'plan.json');spec=read('docs/prototype/mechanical/pololu_mount_fasteners/rear_candidate.json');place=read('validation/pololu_rear_bracket_v2/report.json')['rear_plate_proposed_holes_yz_mm'];root=Path('validation/yaw_integrated_candidate_v7');items=read(root/'inventory.json')['parts'];sp=root/'yaw_support_candidate.step';paths.append(sp);ss=cq.importers.importStep(str(sp)).val().Solids();assert len(ss)==len(items)==52;targets={i['name']:s for i,s in zip(items,ss)};plate=targets['rear_plate'];old_plate_volume=plate.Volume();hardware={};groups={}
for side,h in place.items():
 y=h[0][0];bp=Path('validation/pololu_captive_nut_v1')/(side+'_bracket.step');paths.append(bp);b=cq.importers.importStep(str(bp)).val()
 for z in plan['old_z_mm']:b=b.fuse(cyl(1.7,4,-62.2,y,z))
 for i,z in enumerate(plan['new_z_mm']):
  b=b.cut(cyl(1.7,10,-65,y,z));plate=plate.cut(cyl(1.7,10,-65,y,z));g=f'{side}_{i}'
  sc=spec['screw'];wa=spec['washer'];nu=spec['nut'];seat=-64.2-wa['thickness_mm'];inner=-58.2;nx=inner+wa['thickness_mm']
  screw=cyl(1.5,sc['length_mm'],seat,y,z).fuse(cyl(sc['head_diameter_mm']/2,sc['head_height_mm'],seat-sc['head_height_mm'],y,z))
  outer=cyl(wa['outer_diameter_mm']/2,wa['thickness_mm'],seat,y,z).cut(cyl(wa['inner_diameter_mm']/2,wa['thickness_mm'],seat,y,z))
  inside=cyl(wa['outer_diameter_mm']/2,wa['thickness_mm'],inner,y,z).cut(cyl(wa['inner_diameter_mm']/2,wa['thickness_mm'],inner,y,z))
  R=nu['across_flats_mm']/math.sqrt(3);v=[(y+R*math.cos(k*math.pi/3),z+R*math.sin(k*math.pi/3)) for k in range(6)]
  nut=cq.Workplane('YZ').workplane(offset=nx).polyline(v).close().extrude(nu['height_mm']).val().cut(cyl(1.5,nu['height_mm'],nx,y,z))
  for n,s in [('screw',screw),('outer_washer',outer),('inner_washer',inside),('nut',nut)]:hardware[g+'_'+n]=s;groups[g+'_'+n]=(side,i,n)
 b=b.clean();assert len(b.Solids())==1 and b.isValid();targets[side+'_power_bracket']=b;cq.exporters.export(b,str(a.out/(side+'_bracket.step')))
targets['rear_plate']=plate;cq.exporters.export(plate,str(a.out/'rear_plate.step'))
for n,f in {'tray':'board/mechanical/prototype/rc_battery_tray_revB/tray.step','battery':'validation/rc_battery_cad_v1_checked/battery_candidate.step','Tab5':'software/sim/mujoco/assets/r9_fast_turn_v1/cad/Tab5.step','TTL':'software/sim/mujoco/assets/r9_fast_turn_v1/cad/TTL_interface.step','left_module':'validation/dual_pololu_mounted_layout_v1/left_envelope.step','right_module':'validation/dual_pololu_mounted_layout_v1/right_envelope.step'}.items():paths.append(Path(f));targets[n]=cq.importers.importStep(f).val()
rows=[]
for name,s in hardware.items():
 side,i,kind=groups[name]
 for tn,t in targets.items():
  intended=(kind=='screw' and tn in ['rear_plate',side+'_power_bracket']) or (kind=='outer_washer' and tn=='rear_plate') or (kind=='inner_washer' and tn==side+'_power_bracket')
  rows.append({'part':name,'obstacle':tn,'intended_contact_or_bore':intended,'overlap_mm3':s.intersect(t).Volume(),'distance_mm':s.distance(t)})
for (n,s),(m,t) in itertools.combinations(hardware.items(),2):rows.append({'part':n,'obstacle':m,'intended_contact_or_bore':groups[n][:2]==groups[m][:2],'overlap_mm3':s.intersect(t).Volume(),'distance_mm':s.distance(t)})
bad=[r for r in rows if r['overlap_mm3']>plan['criteria']['max_overlap_mm3'] or (not r['intended_contact_or_bore'] and r['distance_mm']<plan['criteria']['minimum_unintended_gap_mm'])]
expected=4*math.pi*1.7**2*2;removed=old_plate_volume-plate.Volume();assert abs(removed-expected)<1e-5
cq.exporters.export(cq.Compound.makeCompound([plate,targets['left_power_bracket'],targets['right_power_bracket']]+list(hardware.values())),str(a.out/'rear_joint.step'))
r={'checks':rows,'failed_checks':bad,'nominal_fit_pass':not bad,'plate_removed_mm3':removed,'hole_pitch_mm':8,'nominal_thread_tip_protrusion_mm':seat+sc['length_mm']-(nx+nu['height_mm']),'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},'manufacturing_release':False};(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'checks':len(rows),'failures':bad,'plate_removed_mm3':removed},indent=2))
