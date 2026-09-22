"""Recessed metal case-mount plate concept with separate support fastener axes."""
import argparse,json,hashlib
from pathlib import Path
import cadquery as cq
ROOT=Path(__file__).resolve().parents[3];p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--wide-plate',action='store_true');p.add_argument('--relocated-axes',action='store_true');p.add_argument('--front-axis-mm',type=float,default=7.5);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
width,depth,x0=(a.front_axis_mm+41,33,-37.5) if a.relocated_axes else ((45,33,-35) if a.wide_plate else (42,30,-33.5))
plan={'question':'Can a separate 1 mm plate lower the case screw seat by 2 mm without moving servo or thinning its printed screw seat?', 'stop':'One nominal topology, both supports; verify solids, contact and holes; no strength claim.', 'design_assumptions':{'metal_plate_mm':[width,depth,1],'material_candidate':'SUS304, grade and manufacturing tolerance not released','pocket_side_gap_mm':.2,'case_head_access_diameter_mm':5,'clearance_holes_mm':2.3,'plate_support_fasteners':'four M2 through-bolts per plate, exact bolt/nut/washer and preload TBD'}, 'limits':['Plate bending and support pull-through unverified','Screw head and tool dimensions provisional','Metal density 8000 kg/m3 assumed','No manufacturer screw insertion-depth guarantee','No assembled fastener envelopes']};(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');rows=[]
for side,cy in [('left',26),('right',-26)]:
 src=ROOT/f'validation/yaw_case_mount_v2/{side}_yaw_fixed_support.step';support=cq.importers.importStep(str(src)).val();old=support.Volume()
 if a.relocated_axes:support=support.fuse(cq.Solid.makeBox(a.front_axis_mm-6.49,36,3,cq.Vector(9.99,cy-18,88)))
 plate=cq.Solid.makeBox(width,depth,1,cq.Vector(x0,cy-depth/2,88))
 support=support.cut(cq.Solid.makeBox(width+.4,depth+.4,1,cq.Vector(x0-.2,cy-depth/2-.2,88)))
 case_axes=[(x,y) for x in [-27.5,2.5] for y in [cy-8,cy+8]]
 mounting_axes=[(x,y) for x in ([-34,a.front_axis_mm] if a.relocated_axes else [-31.5,6.5]) for y in ([cy-10,cy+10] if a.relocated_axes else [cy-13,cy+13])]
 for x,y in case_axes:
  plate=plate.cut(cq.Solid.makeCylinder(1.15,1.02,cq.Vector(x,y,87.99)))
  support=support.cut(cq.Solid.makeCylinder(2.5,2.02,cq.Vector(x,y,88.99)))
 for x,y in mounting_axes:
  hole=cq.Solid.makeCylinder(1.15,3.02,cq.Vector(x,y,87.99));plate=plate.cut(hole);support=support.cut(hole)
 plate=plate.clean();support=support.clean();assert all(s.isValid() and len(s.Solids())==1 for s in [plate,support])
 overlap=plate.intersect(support).Volume();assert overlap<.01
 for n,s in [('mount_plate',plate),('yaw_fixed_support',support)]:cq.exporters.export(s,str(a.out/f'{side}_{n}.step'))
 rows.append({'side':side,'case_screw_seat_z_mm':89,'nominal_pilot_entry_mm':8-1-4.5,'case_axes':case_axes,'plate_support_axes':mounting_axes,'plate_volume_mm3':plate.Volume(),'plate_mass_kg_assumed':plate.Volume()*8e-6,'support_volume_removed_mm3':old-support.Volume(),'plate_support_overlap_mm3':overlap,'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest()})
r={'rows':rows,'manufacturing_release':False,'strength_verified':False,'limits':plan['limits']};(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
