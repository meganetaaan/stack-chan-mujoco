import json
from pathlib import Path
p=Path(__file__).resolve().parent
plan=json.loads((p/'traction_plan.json').read_text())
rows=[]
for h in plan['mesh_sizes_mm']:
    r=json.loads((p/f'traction_{h}/report.json').read_text())
    rows.append({'mesh_mm':h,'relative_equilibrium_error':r['stress_traction_vs_reaction_relative_error'],'equilibrium_diagnostic_pass':r['stress_traction_vs_reaction_relative_error'] <= plan['stress_integral_vs_assembled_reaction_relative_error_max'],'sampled_tension_detected':r['tension_detected_in_stress_samples']})
(p/'traction_verdict.json').write_text(json.dumps({'rows':rows,'finest_equilibrium_diagnostic_pass':rows[-1]['equilibrium_diagnostic_pass'],'unilateral_contact_verified':False},indent=2)+'\n')
