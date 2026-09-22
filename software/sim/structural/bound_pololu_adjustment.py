"""Necessary fit and anti-rotation bounds; not a proof of complete joint fit."""
import json,math,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
paths=[ROOT/'docs/prototype/mechanical/pololu_mount_fasteners/candidate.json',ROOT/'docs/prototype/mechanical/yaw_hex_nut/candidate.json']
a,b=[json.loads(p.read_text()) for p in paths]
Dpcb=2.18;Dscrew=2.;Dbracket=2.2
pcb_r=(Dpcb-Dscrew)/2;bracket_r=(Dbracket-Dscrew)/2
W=a['assumptions']['pocket_width_x_mm'];AF=a['nut']['across_flats_mm'];corner=b['across_corners_min_catalog_mm']
nut_float=(W-AF)/2
# For diagonal error (E,E), the smallest required adjustment in either
# coordinate is E-rPCB/sqrt(2). Circular bracket bores bound the vector norm.
Emax=min((pcb_r+bracket_r)/math.sqrt(2), nut_float+pcb_r/math.sqrt(2))
rows=[]
for print_error in [0,.025,.05,.1]:
 E=.1+print_error
 required_coord=max(0,E-pcb_r/math.sqrt(2))
 rows.append({'assumed_print_location_error_per_axis_mm':print_error,
  'combined_diagonal_error_per_axis_mm':E,
  'required_adjustment_per_axis_mm':required_coord,
  'necessary_bracket_bore_diameter_mm':Dscrew+2*math.sqrt(2)*required_coord,
  'necessary_pocket_width_mm':AF+2*required_coord,
  'pocket_width_window_below_catalog_corner_min_mm':corner-(AF+2*required_coord),
  'current_nominal_necessary_fit_condition':E<=Emax})
out=ROOT/'validation/pololu_adjustment_bounds_v1';out.mkdir(exist_ok=True)
plan={'scope':__doc__,'stop':'Analytic necessary conditions only; do not enlarge pockets or choose a manufacturing tolerance to force a pass.',
 'assumptions':['All listed bore/shaft/AF sizes nominal; tolerances unknown','PCB position +/-0.1mm Cartesian','Bracket bore and nut pocket concentric; no relative error','Rigid perpendicular screws and equal diagonal error','Print errors are sensitivity inputs, not claimed printer capability'],
 'relations':['sqrt(2)*E <= rPCB+rBracket','E <= (W-AF)/2+rPCB/sqrt(2)','W < nut across-corners minimum is necessary to rule out free in-plane nut rotation in an open parallel-wall slot'],
 'excluded':['Nut torque capacity, tilt, chamfers, insertion, retention','Bore/pocket size errors and eccentricity','Seat strength, preload and creep']}
(out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
r={'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
 'nominal_PCB_radial_clearance_mm':pcb_r,'nominal_bracket_radial_clearance_mm':bracket_r,
 'nominal_nut_X_float_mm':nut_float,'current_diagonal_error_per_axis_upper_bound_mm':Emax,
 'remaining_print_error_per_axis_upper_bound_mm':Emax-.1,'rows':rows,
 'decision':'Current candidate has little tolerance budget. Do not widen nut pocket without separately checking rotation restraint.',
 'complete_fit_proven':False,'manufacturing_release':False}
(out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
