"""CAD insertion and height-stack screen for pause-and-insert rear hardware."""
import argparse,hashlib,json
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
build=json.loads((a.candidate/'plan.json').read_text());assert build['loading_mode']=='embedded'
body=cq.importers.importStep(str(a.candidate/'body_shroud.step')).val()
plan={'scope':__doc__,'build_base_x_mm':-62.2,'print_direction':'+X','layer_height_mm':.2,'pause_after_height_mm':8.8,'pause_plane_x_mm':-53.4,
      'sequence':['print cavity walls, pause before roof layers','drop four reduced-diameter washers axially','place four aligned square nuts','verify full seating and remove temporary tools','resume roof and remaining body'],
      'criteria':{'intersection_mm3':.01,'hardware_below_pause_plane_mm':.2,'minimum_total_fit_mm':.1},
      'body_surface_tolerance_mm':.2,'seat_x_mm':-56.2,'nut_thickness_max_mm':build['nut']['thickness_max_mm'],
      'washer_thickness_max_mm':build['inner_washer']['thickness_mm'][1],
      'source_sha256':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in [a.candidate/'body_shroud.step',a.candidate/'plan.json']},
      'limitations':['CAD stage clipping, not slicer G-code verification','uniform 0.2mm layers assumed','fully seated and aligned hardware assumed','nozzle-tip height only; printer head, thermal, bridge and adhesion behavior unverified','screw engagement and retention strength remain unverified']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
printed=body.intersect(cq.Solid.makeBox(9.6,140,140,cq.Vector(-63,-70,-6))) # ends at -53.4
assert abs(printed.BoundingBox().xmax+53.4)<1e-6
cq.exporters.export(printed,str(a.out/'printed_at_pause.step'))
print_oriented=body.rotate((0,0,0),(0,1,0),-90).translate((128,64,62.2))
cq.exporters.export(print_oriented,str(a.out/'body_print_orientation.step'))
b=print_oriented.BoundingBox();assert abs(b.zmin)<1e-6 and abs(b.xlen-128)<1e-6 and abs(b.ylen-128)<1e-6
rows=[]
for i,(y,z) in enumerate(( (sign*57,z) for sign in [-1,1] for z in [8,120])):
    for name,start,end,width in [('washer',-56.2,-50,6.),('nut',-55.7,-50,5.5)]:
        sweep=cq.Solid.makeCylinder(3,end-start,cq.Vector(start,y,z),cq.Vector(1,0,0)) if name=='washer' else cq.Solid.makeBox(end-start,width,width,cq.Vector(start,y-width/2,z-width/2))
        overlap=float(sweep.intersect(printed).Volume())
        rows.append({'corner':i,'part':name,'sweep_overlap_mm3':overlap,'passed':overlap<=.01})
        cq.exporters.export(sweep,str(a.out/f'{i}_{name}_insertion.step'))
    washer=cq.importers.importStep(str(a.candidate/f'corner_{i}_inner_washer.step')).val()
    rows.append({'corner':i,'part':'washer_seat','distance_mm':float(washer.distance(body)),'overlap_mm3':float(washer.intersect(body).Volume()),'passed':bool(washer.distance(body)<1e-6 and washer.intersect(body).Volume()<=.01)})
maximum_top=plan['seat_x_mm']+.2+plan['washer_thickness_max_mm']+plan['nut_thickness_max_mm']
clearance=plan['pause_plane_x_mm']-maximum_top
width_min=build['pocket']['width_z_mm']-.4
fit={'washer_total_width_gap_mm':width_min-build['inner_washer']['OD_mm'][1],
     'nut_total_width_gap_mm':width_min-build['nut']['width_max_mm'],
     'stack_total_depth_gap_mm':build['pocket']['thickness_x_mm']-.4-plan['washer_thickness_max_mm']-plan['nut_thickness_max_mm']}
gates={'insertion_and_seating':all(r['passed'] for r in rows),'hardware_height':clearance>=.2-1e-9,'fit':all(v>=.1-1e-9 for v in fit.values())}
report={'scope':__doc__,'rows':rows,'fit':fit,'worst_hardware_top_x_mm':maximum_top,'worst_clearance_below_pause_mm':clearance,
        'gates':gates,'passed_geometry_screen':all(gates.values()),'manufacturing_release':False,'joint_strength_verified':False}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='rows'}))
