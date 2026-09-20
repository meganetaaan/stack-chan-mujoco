"""Continuous axis-aligned sweep of a candidate spring-finger nut-loading jig."""
import argparse,hashlib,json
from pathlib import Path
import cadquery as cq
ROOT=Path(__file__).resolve().parents[3]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--body',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--path-mode',choices=['direct','lift20','lift14'],default='lift14');p.add_argument('--fastener-check',choices=['on','off'],default='on')
a=p.parse_args();lateral=14 if a.path_mode=='lift14' else 20;lower_lift=0 if a.path_mode=='direct' else 52
a.out.mkdir(parents=True,exist_ok=False)
body_plan_path=a.body.parent/'plan.json'
body_plan=json.loads(body_plan_path.read_text())
slot_width=body_plan['pocket']['width_z_mm']
assert body_plan['pocket']['thickness_x_mm']==2.4 and body_plan['pocket']['nut_back_x_mm']==-55.7
plate=ROOT/'validation/rear_joint_assembly_development_v1/rear_joint_socket_double_v1/rear_structural_plate.step'
parts={'body':cq.importers.importStep(str(a.body)).val(),'rear_plate':cq.importers.importStep(str(plate)).val()}
plan={'scope':__doc__,'stage':'bare body and rear plate, before Tab5, yaw supports, battery and power installation',
      'source_sha256':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in [a.body,plate,body_plan_path]},
      'pocket_width_mm':slot_width,'jaw_thickness_mm':.1,'jaw_thickness_upper_mm':.12,'jaw_material':'spring sheet candidate; alloy, stress and grip force not verified',
      'shaft_section_mm':[2,2],'shaft_end_x_mm':80,'handle_end_x_mm':125,
      'path_mode':a.path_mode,'fastener_check':a.fastener_check,'lateral_travel_mm':lateral,'lower_tool_offset_mm':lower_lift,'lower_approach_lift_mm':lower_lift,
      'stages':[f'axial approach at y=+/-{57-lateral}, lower nuts raised {lower_lift} mm','lower inside body',f'{lateral} mm outward slide to y=+/-57','reverse slide after bolt engagement','raise lower jig','axial withdrawal'],
      'criteria':{'intersection_mm3':.01,'functional_total_gap_mm':.1,'free_tool_clearance_mm':.5},
      'body_surface_tolerance_mm':.2,'rigid_tool_surface_tolerance_mm':.2,
      'limitations':['kinematic geometry only','finger spring deflection, retention and release force not verified','no hand or cable geometry','fixed clamped-open finger shape during withdrawal','assembled fasteners require separate contact/strength checks']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
def box_bounds(bounds):
 x0,x1,y0,y1,z0,z1=bounds
 return cq.Solid.makeBox(x1-x0,y1-y0,z1-z0,cq.Vector(x0,y0,z0))
def moved(b,dx=0,dy=0,dz=0):return [b[0]+dx,b[1]+dx,b[2]+dy,b[3]+dy,b[4]+dz,b[5]+dz]
def swept(b,axis,lo,hi):
 c=list(b);c[2*axis]+=lo;c[2*axis+1]+=hi;return c
fasteners={}
for i in (range(4) if a.fastener_check=='on' else []):
    for name in ['nut','bolt','inner_washer']:
        path=a.body.parent/f'corner_{i}_{name}.step'
        fasteners[i,name]=cq.importers.importStep(str(path)).val()
        plan['source_sha256'][str(path)]=hashlib.sha256(path.read_bytes()).hexdigest()
plan['fastener_staging']='Other corner nuts/bolts and all inner washers included; target nut and bolt included after engagement.' if a.fastener_check=='on' else 'Fasteners omitted for historical route comparison only.'
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
rows=[]
for sign in [-1,1]:
 for z in [8,120]:
    corner=(0 if sign<0 else 2)+(0 if z==8 else 1)
    boxes={'nut':[-55.7,-53.9,54.25,59.75,z-2.75,z+2.75],
           'upper_finger':[-55.7,-53.9,51,59.75,z+2.75,z+2.85],
           'lower_finger':[-55.7,-53.9,51,59.75,z-2.85,z-2.75],
           'hub':[-55.7,-53.9,49,51,z-2.85,z+2.85],
           'shaft':[-53.9,80,49,51,z-1,z+1],
           'handle':[80,125,45,55,z-5,z+5]}
    lift=lower_lift if z==8 else 0
    if lift:
        boxes['stem']=[-53.9,-51.9,49,51,z-1,z+lift+1]
        boxes['shaft']=[-51.9,80,49,51,z+lift-1,z+lift+1]
        boxes['handle']=[80,125,45,55,z+lift-5,z+lift+5]
    # Build on +Y and reflect the complete geometry for the opposite side.
    for name,b in boxes.items():
        shape=box_bounds(b)
        if sign<0:shape=shape.mirror('XZ')
        cq.exporters.export(shape,str(a.out/f'{sign}_{z}_{name}.step'))
    for stage in (['approach','lower','slide','release','raise','withdraw'] if lift else ['approach','slide','release','withdraw']):
      for name,b in boxes.items():
        if stage in ['release','raise','withdraw'] and name=='nut':continue
        if stage in ['approach','withdraw']:bound=swept(moved(b,dy=-lateral,dz=lift),0,0,120.7)
        elif stage in ['lower','raise']:bound=swept(moved(b,dy=-lateral),2,0,lift)
        else:bound=swept(b,1,-lateral,0)
        shape=box_bounds(bound)
        if sign<0:shape=shape.mirror('XZ')
        clashes=[];closest=1e9
        staged=dict(parts)
        for (i,kind),fixed in fasteners.items():
            if i!=corner or kind=='inner_washer' or stage in ['release','raise','withdraw']:
                staged[f'corner_{i}_{kind}']=fixed
        for part,fixed in staged.items():
            distance=float(shape.distance(fixed));closest=min(closest,distance)
            if distance<1e-6:
                volume=float(shape.intersect(fixed).Volume())
                if volume>.01:clashes.append({'part':part,'volume_mm3':volume})
        rows.append({'side':sign,'z_mm':z,'stage':stage,'component':name,'clashes':clashes,'minimum_nominal_distance_mm':closest,
                     'free_tool_clearance_passed':bool(closest-.4>=.5) if name in ['hub','stem','shaft','handle'] else None})
# Worst manufactured slot width minus largest nut plus both thickest fingers.
fit=slot_width-2*body_plan['pocket']['surface_tolerance_mm']-body_plan['nut']['width_max_mm']-2*.12
report={'scope':__doc__,'rows':rows,'functional_width_gap_worst_mm':fit,'functional_width_passed':bool(fit>=.1),
        'interference_count':sum(len(r['clashes']) for r in rows),'free_tool_clearance_failures':sum(r['free_tool_clearance_passed'] is False for r in rows),
        'assembly_verified':False,'manufacturing_release':False}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='rows'}))
