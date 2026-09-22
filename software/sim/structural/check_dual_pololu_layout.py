"""Replace legacy UBEC boxes at their existing centers with Pololu catalog envelopes."""
import argparse,hashlib,json
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
specpath=Path('schematics/power/dual_pololu_candidate.json');spec=json.loads(specpath.read_text());placement=Path('validation/dual_ubec_layout_v2/report.json');centers=json.loads(placement.read_text())['centers_mm'];root=Path('validation/yaw_integrated_candidate_v7');ip=root/'inventory.json';sp=root/'yaw_support_candidate.step';paths=[specpath,placement,ip,sp]
# Long edge follows X, matching old UBEC. Rounded metric dimensions are not tolerances.
mechanical=Path('schematics/power/dual_pololu_mechanical.json');md=json.loads(mechanical.read_text());paths.append(mechanical)
# Allow each opposite board edge its stated location tolerance.
dims=[md['board_xy'][1]+2*md['board_edge_tolerance'],md['board_xy'][0]+2*md['board_edge_tolerance'],md['total_nominal_height']]
plan={'question':'Can two catalog module envelopes replace old UBEC centers without fixed-part overlap?','centers_mm':centers,'dimensions_xyz_mm':dims,'dimension_source':'reg34c drawing: board edge tolerance expanded on both edges; total height6.1+1.57+1.8mm, height tolerance unknown','criterion_overlap_mm3':.01,'stop':'One orientation and placement; no search or mount design.','limits':['Board edge allowance included; height tolerance and mounting displacement not covered','No wires, terminal blocks, insulation, mounts or thermal clearance','No dynamic or extraction clearance','Legacy UBEC boxes are removed, not additional obstacles'],'manufacturing_release':False}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
items=json.loads(ip.read_text())['parts'];solids=cq.importers.importStep(str(sp)).val().Solids();assert len(items)==len(solids)==52;targets={}
for item,s in zip(items,solids):
 assert abs(item['volume_mm3']-s.Volume())<1e-5
 targets[item['name']]=s
extra={'tray':'board/mechanical/prototype/rc_battery_tray_revB/tray.step','battery':'validation/rc_battery_cad_v1_checked/battery_candidate.step','Tab5':'software/sim/mujoco/assets/r9_fast_turn_v1/cad/Tab5.step','TTL':'software/sim/mujoco/assets/r9_fast_turn_v1/cad/TTL_interface.step'}
for n,f in extra.items():paths.append(Path(f));targets[n]=cq.importers.importStep(f).val()
modules={};rows=[]
for side,c in zip(['left','right'],centers):
 s=cq.Solid.makeBox(*dims,cq.Vector(*[c[i]-dims[i]/2 for i in range(3)]));modules[side]=s;cq.exporters.export(s,str(a.out/(side+'.step')))
 for name,t in targets.items():rows.append({'module':side,'part':name,'overlap_mm3':s.intersect(t).Volume(),'distance_mm':s.distance(t)})
rows.append({'module':'left','part':'right_module','overlap_mm3':modules['left'].intersect(modules['right']).Volume(),'distance_mm':modules['left'].distance(modules['right'])})
r={'checks':rows,'collisions':[x for x in rows if x['overlap_mm3']>.01],'minimum_nominal_distance_mm':min(x['distance_mm'] for x in rows),'source_sha256':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in paths},'manufacturing_release':False}
(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'checks':len(rows),'collisions':r['collisions'],'min_mm':r['minimum_nominal_distance_mm']},indent=2))
