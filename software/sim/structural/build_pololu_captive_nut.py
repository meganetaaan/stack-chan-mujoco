"""Design comparison of side-loaded captive nut pockets and selected fasteners."""
import argparse,hashlib,json,math
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();paths=[]
def read(p):
 p=Path(p);paths.append(p);return json.loads(p.read_text())
plan=read(a.out/'plan.json');spec=read('docs/prototype/mechanical/pololu_mount_fasteners/candidate.json');pl=read('validation/dual_pololu_mounted_layout_v1/report.json')['placements'];cfg=spec['assumptions'];root=Path('validation/yaw_integrated_candidate_v7');items=read(root/'inventory.json')['parts'];sp=root/'yaw_support_candidate.step';paths.append(sp);ss=cq.importers.importStep(str(sp)).val().Solids();assert len(ss)==len(items)==52;targets={i['name']:s for i,s in zip(items,ss)}
for n,f in {'tray':'board/mechanical/prototype/rc_battery_tray_revB/tray.step','battery':'validation/rc_battery_cad_v1_checked/battery_candidate.step','Tab5':'software/sim/mujoco/assets/r9_fast_turn_v1/cad/Tab5.step','TTL':'software/sim/mujoco/assets/r9_fast_turn_v1/cad/TTL_interface.step'}.items():
 paths.append(Path(f));targets[n]=cq.importers.importStep(f).val()
rows=[];summaries=[];fasteners=[]
for place in pl:
 side=place['side'];bp=Path('validation/pololu_rear_bracket_v2')/(side+'_bracket.step');paths.append(bp);old=cq.importers.importStep(str(bp)).val();s=old;hardware=[]
 for idx,(x,y,zpcb) in enumerate(place['mount_axes_mm']):
  slot=cq.Solid.makeBox(cfg['pocket_width_x_mm'],8,cfg['pocket_top_z_mm']-cfg['pocket_bottom_z_mm'],cq.Vector(x-cfg['pocket_width_x_mm']/2,y-4,cfg['pocket_bottom_z_mm']));s=s.cut(slot)
  R=spec['nut']['across_flats_mm']/math.sqrt(3);verts=[(x+R*math.cos(math.radians(30+60*k)),y+R*math.sin(math.radians(30+60*k))) for k in range(6)]
  nut=cq.Workplane('XY').workplane(offset=cfg['nut_bottom_z_mm']).polyline(verts).close().extrude(spec['nut']['height_max_mm']).val();nut=nut.cut(cq.Solid.makeCylinder(1,3,cq.Vector(x,y,95)))
  seat=zpcb+1.5748;tip=seat-spec['screw']['length_mm'];screw=cq.Solid.makeCylinder(1,spec['screw']['length_mm'],cq.Vector(x,y,tip)).fuse(cq.Solid.makeCylinder(spec['screw']['head_diameter_mm']/2,spec['screw']['head_height_mm'],cq.Vector(x,y,seat)))
  protr=cfg['nut_bottom_z_mm']-tip
  hardware += [(f'{side}_{idx}_nut',nut),(f'{side}_{idx}_screw',screw)]
  fasteners.append({'side':side,'index':idx,'screw_tip_z_mm':tip,'nut_z_mm':[cfg['nut_bottom_z_mm'],cfg['pocket_top_z_mm']],'geometric_tip_protrusion_mm':protr,'tip_screen_pass':protr>=plan['criteria']['minimum_geometric_tip_protrusion_mm']})
 s=s.clean();assert s.isValid() and len(s.Solids())==1
 upper=old.intersect(cq.Solid.makeBox(100,150,30,cq.Vector(-70,-75,cfg['pocket_top_z_mm'])))
 lost=upper.cut(s).Volume();assert lost<=plan['criteria']['upper_layer_loss_mm3']
 cq.exporters.export(s,str(a.out/(side+'_bracket.step')))
 cq.exporters.export(cq.Compound.makeCompound([s]+[h for n,h in hardware]),str(a.out/(side+'_with_fasteners.step')))
 summaries.append({'side':side,'volume_mm3':s.Volume(),'upper_layer_lost_mm3':lost,'roof_above_pocket_mm':102.065-cfg['pocket_top_z_mm'],'connected_solids':len(s.Solids())})
 for name,h in hardware:
  rows.append({'part':name,'obstacle':'own_bracket','overlap_mm3':h.intersect(s).Volume(),'distance_mm':h.distance(s),'intended_contact':True})
  for tn,t in targets.items():rows.append({'part':name,'obstacle':tn,'overlap_mm3':h.intersect(t).Volume(),'distance_mm':h.distance(t),'intended_contact':False})
bad=[r for r in rows if r['overlap_mm3']>plan['criteria']['maximum_unintended_overlap_mm3'] or (not r['intended_contact'] and r['distance_mm']<plan['criteria']['minimum_other_part_clearance_mm'])]
r={'summaries':summaries,'fasteners':fasteners,'checks':rows,'failed_checks':bad,'screen_pass':not bad and all(x['tip_screen_pass'] for x in fasteners),'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},'manufacturing_release':False};(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'summaries':summaries,'failures':bad,'fastener_example':fasteners[0]},indent=2))
