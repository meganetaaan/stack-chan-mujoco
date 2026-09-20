"""Nominal stack and declared manufacturing sensitivity; not a strength check."""
import json
from pathlib import Path
out=Path(__file__).resolve().parent
plan={'nut_width_mm':[3.7,4.0],'nut_thickness_mm':[.8,1.2],'cavity_width_mm':4.4,'cavity_height_mm':1.8,'cavity_floor_z_mm':-14.6,'head_seat_z_mm':-19,'screw_nominal_length_mm':6,'head_diameter_max_mm':3.8,'head_height_max_mm':2,'head_pocket_radius_mm':2.3,'head_pocket_depth_mm':2.2,'assumed_print_surface_error_mm':.2,'criteria':{'minimum_head_axial_residual_mm':.2,'minimum_head_radial_residual_mm':.2,'positive_full_nut_height_coverage':True},'limitations':['Screw length tolerance, chamfer and incomplete thread allowances not supplied; nominal length only.','Print error is a design sensitivity assumption, not a qualified process.','Geometric nut height coverage is not effective thread engagement or proof strength.']}
(out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
end=plan['head_seat_z_mm']+plan['screw_nominal_length_mm']
rows=[]
for error in (0,.2):
 axial=plan['head_pocket_depth_mm']-plan['head_height_max_mm']-error
 radial=plan['head_pocket_radius_mm']-plan['head_diameter_max_mm']/2-error
 nut_top=plan['cavity_floor_z_mm']+max(plan['nut_thickness_mm'])
 rows.append({'assumed_print_error_mm':error,'head_axial_residual_mm':axial,'head_radial_residual_mm':radial,'nut_projection_nominal_mm':end-nut_top,'head_clearance_pass':axial>=.2-1e-9 and radial>=.2-1e-9,'nominal_nut_height_covered':end>=nut_top})
(out/'report.json').write_text(json.dumps({'rows':rows,'manufacturing_release':False},indent=2)+'\n')
print(json.dumps(rows,indent=2))
