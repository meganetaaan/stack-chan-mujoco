"""Check the predefined three-mesh displacement/stress convergence gate."""
import argparse,json,hashlib
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--analyses',type=Path,nargs='+',required=True)
p.add_argument('--out',type=Path,required=True)
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
rows=[];identity=None
for folder in a.analyses:
    plan=json.loads((folder/'plan.json').read_text())
    report=json.loads((folder/'report.json').read_text())
    current={k:plan[k] for k in ['geometry_sha256','young_MPa','poisson','criteria','fixed','load','wrenches_N_Nmm','selected_time_s']}
    if identity is None:identity=current
    assert current==identity,'Different geometry, loading, constraints, material or criteria'
    case=next(r for r in report['rows'] if r['name']=='simultaneous')
    rows.append({'mesh_mm':plan['mesh_mm'],'displacement_mm':case['max_displacement_mm'],
                 'principal_MPa':case['max_absolute_principal_MPa'],'von_mises_MPa':case['max_von_mises_MPa'],
                 'screen_passed':report['passed_screen'],
                 'source_hashes':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in [folder/'plan.json',folder/'report.json']}})
rows.sort(key=lambda r:-r['mesh_mm'])
assert len(rows)>=3 and len({r['mesh_mm'] for r in rows})==len(rows),'At least three distinct mesh sizes required'
changes={key:abs(rows[-1][key]-rows[-2][key])/max(abs(rows[-1][key]),1e-30) for key in ['displacement_mm','principal_MPa','von_mises_MPa']}
gates={'three_meshes':len(rows)>=3,'displacement_convergence':changes['displacement_mm']<=.05,
       'principal_convergence':changes['principal_MPa']<=.1,'von_mises_convergence':changes['von_mises_MPa']<=.1,
       'all_mesh_screens':all(r['screen_passed'] for r in rows)}
result={'scope':__doc__,'criteria':{'relative_displacement':.05,'relative_stress':.1},
        'relative_change_denominator':'finest mesh absolute maximum','rows':rows,'last_two_relative_changes':changes,
        'gates':gates,'passed':all(gates.values()),'load_path_verified':False,
        'limitations':['single recorded instant','ideal corner clamps','extra plate mass absent from dynamic loads','contact, joint compliance and buckling not represented']}
(a.out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
