"""Screen slot tolerances with supplier nut dimensional limits."""
import json,math
from pathlib import Path
nut=json.loads(Path('docs/prototype/mechanical/boot_fasteners/nut_candidate.json').read_text())
error=json.loads(Path('validation/boot_low_head_candidate_v1/plan.json').read_text())['print_error_assumption_mm']
rows=[]
for rev in ('v1','v2'):
 p=json.loads(Path(f'validation/boot_nut_side_entry_{rev}/plan.json').read_text())
 width=p['slot_width_mm'];height=p['slot_z_mm'][1]-p['slot_z_mm'][0]
 rows.append({'revision':rev,'width_mm':width,'height_mm':height,
 'minimum_total_width_clearance_mm':width-2*error-max(nut['across_flats_mm']),
 'minimum_total_height_clearance_mm':height-2*error-max(nut['thickness_mm']),
 'minimum_nut_diagonal_minus_max_channel_width_mm':min(nut['across_flats_mm'])*math.sqrt(2)-(width+2*error)})
report={'rows':rows,'print_boundary_assumption_mm':error,
 'scope':'Centered square envelope and uniform channel, not tool access or qualified friction/anti-rotation strength',
 'manufacturing_release':False}
Path('validation/boot_nut_side_entry_v2/tolerance_budget.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
