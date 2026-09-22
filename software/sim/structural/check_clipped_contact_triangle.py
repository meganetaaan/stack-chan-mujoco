"""Closed-form force/energy and finite-difference tangent checks."""
import argparse,json
from pathlib import Path
import numpy as np
from clipped_contact_triangle import integrate
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
plan={'scope':__doc__,'analytic_absolute_tolerance':1e-12,'tangent_absolute_tolerance':1e-8,'finite_difference_step':1e-6,'reference_triangle_area':.5};(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');rows=[]
for name,g,expected_force,expected_energy,expected_area in [('uniform_compression',[-2,-2,-2],1.,1.,.5),('open',[1,2,3],0.,0.,0.),('half_cut',[-.5,.5,-.5],5/48,7/384,3/8)]:
 r=integrate(g,.5);error=max(abs(r['force'].sum()-expected_force),abs(r['energy']-expected_energy),abs(r['active_area']-expected_area));eps=plan['finite_difference_step'];g=np.array(g,dtype=float);jac=np.column_stack([(integrate(g+eps*np.eye(3)[j],.5)['force']-integrate(g-eps*np.eye(3)[j],.5)['force'])/(2*eps) for j in range(3)]);tangent_error=float(np.max(abs(jac+r['tangent'])));rows.append({'case':name,'analytic_error':float(error),'force_derivative_plus_tangent_error':tangent_error,'passed':bool(error<=1e-12 and tangent_error<=1e-8)})
# Uniform active triangle mass matrix has diagonal A/6, off-diagonal A/12.
r=integrate([-1,-1,-1],.5);expected=.5/12*(np.ones((3,3))+np.eye(3));err=float(abs(r['tangent']-expected).max());rows.append({'case':'full_triangle_matrix','analytic_error':err,'passed':err<=1e-12})
report={'rows':rows,'passed':all(r['passed'] for r in rows),'assembly_and_joint_verified':False};(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));raise SystemExit(0 if report['passed'] else 1)
