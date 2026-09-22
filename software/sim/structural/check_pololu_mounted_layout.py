"""Conservative mounted-module envelope check at fixed candidate positions."""
import argparse, hashlib, json
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser();p.add_argument('step',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
paths=[]
def read(path):
    path=Path(path);paths.append(path);return json.loads(path.read_text())
plan=read(a.out/'plan.json')
md=read('schematics/power/dual_pololu_mechanical.json')
assert hashlib.sha256(a.step.read_bytes()).hexdigest()==md['step_sha256']
paths.append(a.step)
s=cq.importers.importStep(str(a.step)).val();b=s.BoundingBox()
old=read('validation/dual_pololu_layout_v2/plan.json')
mount=read('validation/dual_pololu_mount_space_v1/plan.json')['assumptions']
drill=read('validation/dual_pololu_drill_v1/report.json')
root=Path('validation/yaw_integrated_candidate_v7');items=read(root/'inventory.json')['parts'];sp=root/'yaw_support_candidate.step';paths.append(sp)
solids=cq.importers.importStep(str(sp)).val().Solids();assert len(items)==len(solids)==52
targets={}
for item,solid in zip(items,solids):
    assert abs(item['volume_mm3']-solid.Volume())<1e-5
    targets[item['name']]=solid
for name,path in {'tray':'board/mechanical/prototype/rc_battery_tray_revB/tray.step','battery':'validation/rc_battery_cad_v1_checked/battery_candidate.step','Tab5':'software/sim/mujoco/assets/r9_fast_turn_v1/cad/Tab5.step','TTL':'software/sim/mujoco/assets/r9_fast_turn_v1/cad/TTL_interface.step'}.items():
    paths.append(Path(path));targets[name]=cq.importers.importStep(path).val()
modules={};placements=[];rows=[]
for side,c in zip(['left','right'],old['centers_mm']):
    # PCB underside is 1.8 mm above the old bottom component plane.
    zpcb=c[2]-old['dimensions_xyz_mm'][2]/2+md['component_below_pcb']
    dx,dy=c[0]-drill['board_mm'][0]/2,c[1]-drill['board_mm'][1]/2
    points=[]
    for x,y in drill['mount_centers_mm']:
        points.append([x+dx,y+dy,zpcb])
    halfx=old['dimensions_xyz_mm'][0]/2;halfy=old['dimensions_xyz_mm'][1]/2
    assert c[0]-halfx<=b.xmin+dx and b.xmax+dx<=c[0]+halfx
    assert c[1]-halfy<=b.ymin+dy and b.ymax+dy<=c[1]+halfy
    low=zpcb+min(b.zmin,-mount['spacer_height_mm'])
    high=zpcb+max(b.zmax,1.5748+mount['head_height_mm'],md['pcb_thickness']+md['component_above_pcb'])
    # Verify all cylindrical mount reservations fit the XY envelope.
    for x,y,z in points:
        r=max(mount['spacer_outer_diameter_mm'],mount['head_diameter_mm'])/2
        assert c[0]-halfx<=x-r and x+r<=c[0]+halfx
        assert c[1]-halfy<=y-r and y+r<=c[1]+halfy
    envelope=cq.Solid.makeBox(2*halfx,2*halfy,high-low,cq.Vector(c[0]-halfx,c[1]-halfy,low))
    modules[side]=envelope
    cq.exporters.export(envelope,str(a.out/(side+'_envelope.step')))
    placements.append({'side':side,'step_translation_mm':[dx,dy,zpcb],'pcb_underside_z_mm':zpcb,'mount_axes_mm':points,'envelope_z_mm':[low,high],'envelope_dimensions_mm':[2*halfx,2*halfy,high-low]})
    for name,target in targets.items():
        rows.append({'module':side,'part':name,'overlap_mm3':envelope.intersect(target).Volume(),'distance_mm':envelope.distance(target)})
rows.append({'module':'left','part':'right_module','overlap_mm3':modules['left'].intersect(modules['right']).Volume(),'distance_mm':modules['left'].distance(modules['right'])})
r={'placements':placements,'checks':rows,'collisions':[r for r in rows if r['overlap_mm3']>plan['criterion_overlap_mm3']],'insufficient_clearance':[r for r in rows if r['distance_mm']<plan['criterion_nominal_clearance_mm']],'minimum_distance_mm':min(r['distance_mm'] for r in rows),'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},'manufacturing_release':False}
(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps({k:r[k] for k in ['placements','collisions','insufficient_clearance','minimum_distance_mm']},indent=2))
