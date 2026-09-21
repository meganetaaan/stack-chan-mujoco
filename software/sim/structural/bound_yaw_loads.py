"""Six unit-load FE responses bound every archived yaw wrench by triangle inequality.

A bound exceeding a criterion is inconclusive, not proof of physical failure.
The rear mounting lands are ideally clamped; fasteners/contact are not solved.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from elasticity import tetrahedralize, analyze_many

ROOT=Path(__file__).resolve().parents[3]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--mesh-mm',type=float,default=3.)
    p.add_argument('--step',type=Path,help='Revised left support with the same load and mounting faces')
    p.add_argument('--current-shelf', action='store_true', help='Use the revised plate contact at Z89; stress is diagnostic only')
    a=p.parse_args()
    if a.current_shelf and a.step is None:p.error('--current-shelf requires an explicit revised --step')
    if not np.isfinite(a.mesh_mm) or a.mesh_mm<=0:p.error('positive finite mesh size required')
    a.out.mkdir(parents=True,exist_ok=False)
    source=ROOT/'validation/yaw_connection_development_v1/bolt_group_v1'
    cases=json.loads((source/'report.json').read_text())['rows']
    geometry=a.step.resolve() if a.step else ROOT/'validation/yaw_connection_development_v1/yaw_connection_v1/left_yaw_fixed_support.step'
    paths=[source/(Path(r['source']).parent.name+'_'+r['side']+'.npz') for r in cases]
    criteria={'displacement_mm':.2,'stress_MPa':None if a.current_shelf else 5.6}
    z,xlo,xhi,ylo,yhi=(89.,-37.5,11.6,9.5,42.5) if a.current_shelf else (88.,-29.5,4.5,16.,36.)
    plan={'scope':__doc__,'mesh_mm':a.mesh_mm,'young_MPa':1120.,'poisson':.35,'criteria':criteria,
          'geometry_sha256':hashlib.sha256(geometry.read_bytes()).hexdigest(),
          'geometry':str(geometry.relative_to(ROOT)),
          'fixed':'four rear land faces x=-62.2 mm, ideal clamp',
          'load':f'shelf z={z} mm, x[{xlo},{xhi}], y[{ylo},{yhi}], resultant about [-5,26,62] mm',
          'stop':'Six unit solves at one mesh, then one direct superposition per archived trace at its largest triangle bound. No geometry or threshold changes in this run.',
          'material':'Assumed isotropic E=1120 MPa; actual print grade unknown. Stress is diagnostic only for current shelf; legacy 5.6 MPa threshold is not a certified allowable.',
          'sources':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in paths},
          'limitations':['isotropic linear FE','ideal clamped lands, no cover/bolt contact or buckling',
                         'right loads mirrored to left geometry, symmetric design assumption',
                         'single mesh; convergence not yet proved','triangle bounds may overestimate actual peaks',
                         'selected actual peaks are lower bounds on the archive maximum, not a complete exact maximum',
                         'archived loads do not include latest CAD mass or demonstrate full physical operating envelope']}
    (a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    mesh=tetrahedralize(geometry,a.out/'support.msh',a.mesh_mm)
    coefficients=[];responses=[]
    responses_iter=analyze_many(mesh,lambda x:abs(x[0]+62.2)<1e-6,
        lambda x:(abs(x[2]-z)<1e-6)&(x[0]>=xlo)&(x[0]<=xhi)&(x[1]>=ylo)&(x[1]<=yhi),
        [-5,26,62],np.eye(6),plan['young_MPa'],plan['poisson'])
    for axis,(report,data) in enumerate(responses_iter):
        if report['free_residual_norm_N']>=1e-7 or abs(2*report['strain_energy_Nmm']/report['external_work_Nmm']-1)>=1e-6:
            raise ValueError('Unit response failed equilibrium or energy check')
        coefficients.append([report['max_displacement_mm'],report['max_absolute_principal_MPa'],report['max_von_mises_MPa']])
        responses.append(data['displacement_mm'])
        np.savez_compressed(a.out/f'unit_{axis}.npz',**data)
        (a.out/f'unit_{axis}.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps({'unit_axis':axis,'coefficients':coefficients[-1]}),flush=True)
    coefficients=np.array(coefficients)
    rows=[]
    for case,path in zip(cases,paths):
        with np.load(path) as trace:
            t=trace['time_s'];w=trace['wrench_at_bolt_group_N_Nmm'].copy()
        # Move moments back from bolt-group center to the joint origin.
        side=case['side'];sign=1 if side=='left' else -1
        r=np.array([-5,sign*26,62])-np.array([-60,sign*26,70])
        w[:,3:]-=np.cross(r,w[:,:3])
        if side=='right':
            # Polar force: S F; axial moment: det(S) S M, S=diag(1,-1,1).
            w*=np.array([1,-1,1,-1,1,-1])
        bounds=np.abs(w)@coefficients
        selected=int(bounds[:,0].argmax())
        # Direct vector superposition at the sample with largest displacement bound.
        actual=np.tensordot(w[selected],np.array(responses),axes=(0,0))
        actual_peak=float(np.linalg.norm(actual,axis=1).max())
        row={'source':case['source'],'side':side,'samples':len(t),
             'displacement_upper_mm':float(bounds[:,0].max()),
             'principal_upper_MPa':float(bounds[:,1].max()),'von_mises_upper_MPa':float(bounds[:,2].max()),
             'selected_time_s':float(t[selected]),'selected_wrench_N_Nmm':w[selected].tolist(),
             'selected_actual_displacement_mm':actual_peak,
             'bounded_within_criteria':bool(bounds[:,0].max()<=criteria['displacement_mm'] and (criteria['stress_MPa'] is None or bounds[:,1:].max()<=criteria['stress_MPa']))}
        rows.append(row)
        np.savez_compressed(a.out/(path.stem+'_bounds.npz'),time_s=t,wrench_N_Nmm=w,bounds=bounds)
    report={'scope':__doc__,'rows':rows,'total_samples':sum(r['samples'] for r in rows),
            'max_displacement_upper_mm':max(r['displacement_upper_mm'] for r in rows),
            'max_stress_upper_MPa':max(max(r['principal_upper_MPa'],r['von_mises_upper_MPa']) for r in rows),
            'max_selected_actual_displacement_mm':max(r['selected_actual_displacement_mm'] for r in rows),
            'bounded_within_criteria':all(r['bounded_within_criteria'] for r in rows),
            'production_design_verified':False}
    (a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('scope','rows')}),flush=True)


if __name__=='__main__':main()
