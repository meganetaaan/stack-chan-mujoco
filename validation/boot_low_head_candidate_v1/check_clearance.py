import json
from pathlib import Path
out=Path(__file__).resolve().parent
plan={'head_height_nominal_mm':1.3,'head_diameter_nominal_mm':3.8,'recess_depth_mm':2.2,'recess_radius_mm':2.4,'print_error_assumption_mm':.2,'additional_head_height_assumption_mm':.1,'additional_head_diameter_assumption_mm':.1,'required_residual_mm':.2,'note':'Added dimensional errors are sensitivity assumptions, not supplier tolerances.'}
(out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
rows=[]
for extra in (0,.1):
 axial=2.2-(1.3+extra)-.2
 radial=2.4-(3.8+extra)/2-.2
 rows.append({'additional_screw_dimension_mm':extra,'axial_residual_mm':axial,'radial_residual_mm':radial,'conditional_pass':min(axial,radial)>=.2-1e-9})
(out/'clearance_report.json').write_text(json.dumps({'rows':rows,'manufacturer_tolerance_qualified':False,'manufacturing_release':False},indent=2)+'\n')
print(json.dumps(rows))
