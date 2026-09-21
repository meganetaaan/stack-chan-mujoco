"""Continuous convex-prism sweeps of the proposed side-loaded nut insertion."""
import argparse,hashlib,json,math
from pathlib import Path
import cadquery as cq
import numpy as np
from scipy.spatial import ConvexHull
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();paths=[]
def read(p):
 p=Path(p);paths.append(p);return json.loads(p.read_text())
plan=read(a.out/'plan.json');spec=read('docs/prototype/mechanical/pololu_mount_fasteners/candidate.json');places=read('validation/dual_pololu_mounted_layout_v1/report.json')['placements'];motion=plan['motion'];nut=spec['nut'];root=Path('validation/yaw_integrated_candidate_v7');items=read(root/'inventory.json')['parts'];sp=root/'yaw_support_candidate.step';paths.append(sp);ss=cq.importers.importStep(str(sp)).val().Solids();assert len(ss)==len(items)==52;targets={i['name']:s for i,s in zip(items,ss)}
for n,f in {'tray':'board/mechanical/prototype/rc_battery_tray_revB/tray.step','battery':'validation/rc_battery_cad_v1_checked/battery_candidate.step','Tab5':'software/sim/mujoco/assets/r9_fast_turn_v1/cad/Tab5.step','TTL':'software/sim/mujoco/assets/r9_fast_turn_v1/cad/TTL_interface.step'}.items():
 paths.append(Path(f));targets[n]=cq.importers.importStep(f).val()
rows=[]
for place in places:
 side=place['side'];bp=Path('validation/pololu_captive_nut_v1')/(side+'_bracket.step');paths.append(bp);bracket=cq.importers.importStep(str(bp)).val();mid=sum({v[1] for v in place['mount_axes_mm']})/2
 for i,(x,y,z) in enumerate(place['mount_axes_mm']):
  sign=-1 if y<mid else 1;R=nut['across_flats_mm']/math.sqrt(3);verts=np.array([(x+R*math.cos(math.radians(30+60*k)),y+R*math.sin(math.radians(30+60*k))) for k in range(6)])
  cloud=np.vstack([verts,verts+np.array([0,sign*motion['translation_y_mm']])]);hull=cloud[ConvexHull(cloud).vertices]
  slide=cq.Workplane('XY').workplane(offset=motion['sliding_bottom_z_mm']).polyline([tuple(v) for v in hull]).close().extrude(nut['height_max_mm']).val()
  seat=cq.Workplane('XY').workplane(offset=motion['sliding_bottom_z_mm']).polyline([tuple(v) for v in verts]).close().extrude(nut['height_max_mm']+motion['seated_bottom_z_mm']-motion['sliding_bottom_z_mm']).val()
  swept=slide.fuse(seat)
  own={'sliding_overlap_mm3':slide.intersect(bracket).Volume(),'sliding_gap_mm':slide.distance(bracket),'seating_overlap_mm3':seat.intersect(bracket).Volume()}
  checks=[{'part':n,'overlap_mm3':swept.intersect(t).Volume(),'distance_mm':swept.distance(t)} for n,t in targets.items()]
  ok=own['sliding_overlap_mm3']<=plan['criteria']['maximum_overlap_mm3'] and own['seating_overlap_mm3']<=plan['criteria']['maximum_overlap_mm3'] and own['sliding_gap_mm']+1e-8>=plan['criteria']['minimum_sliding_gap_to_bracket_mm'] and all(c['overlap_mm3']<=plan['criteria']['maximum_overlap_mm3'] and c['distance_mm']>=plan['criteria']['minimum_gap_to_other_parts_mm'] for c in checks)
  rows.append({'side':side,'index':i,'approach_y_sign':sign,'start_center_xy_mm':[x,y+sign*motion['translation_y_mm']],'own_bracket':own,'other_checks':checks,'nominal_path_pass':ok})
r={'paths':rows,'nominal_all_pass':all(r['nominal_path_pass'] for r in rows),'sweep_method':'Convex hull of initial and translated hex prism gives exact continuous translation sweep; bore filled conservatively; vertical seating sweep added','minimum_sliding_gap_mm':min(r['own_bracket']['sliding_gap_mm'] for r in rows),'minimum_other_gap_mm':min(c['distance_mm'] for r in rows for c in r['other_checks']),'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},'manufacturing_release':False};(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:r[k] for k in ['nominal_all_pass','minimum_sliding_gap_mm','minimum_other_gap_mm']},indent=2))
