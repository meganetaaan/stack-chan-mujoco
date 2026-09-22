"""Independent closed-form spring/contact benchmarks for the shared active-set solver."""
import argparse,json
from pathlib import Path
import numpy as np
from scipy.sparse import csr_matrix,diags,eye
from unilateral_contact import solve
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
plan={'scope':__doc__,'absolute_tolerance':1e-10,'cases':['compression_and_opening','gap_below_contact','gap_after_closure','mean_constrained_pair'],'limitations':['Validates contact algebra only; not FE assembly, geometry, contact quadrature, material or finite rotations.']};(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');rows=[]
# Ground springs k=100,200 N/mm; contact gap=g0+u; F=k*u-p*A.
for name,F,g0 in [('compression_and_opening',[-3,4],[0,0]),('gap_below_contact',[-5,-8],[.1,.1]),('gap_after_closure',[-30,-80],[.1,.1])]:
 k=np.array([100.,200.]);F=np.array(F,dtype=float);g0=np.array(g0);area=np.array([2.,3.]);penalty=1000.;free=F/k;closed=g0+free<0;expected=np.where(closed,(F-penalty*area*g0)/(k+penalty*area),free);expected_p=np.where(closed,-penalty*(g0+expected),0)
 r=solve(diags(k),csr_matrix((0,2)),F,eye(2,format='csr'),area,penalty,g0);err=max(np.max(abs(r['u']-expected)),np.max(abs(r['pressure']-expected_p)));rows.append({'case':name,'error':float(err),'passed':bool(err<1e-10 and r['converged']),'history':r['history']})
# Two bodies with common translation removed: u1+u2=0, gap=u1-u2.
# Balanced +/-P and no bulk stiffness: contact force P, gap=-P/(penalty*A).
P=7.;penalty=1000.;area=np.array([2.]);expected=np.array([-P/(2*penalty*area[0]),P/(2*penalty*area[0])]);r=solve(csr_matrix((2,2)),csr_matrix([[.5,.5]]),np.array([-P,P]),csr_matrix([[1.,-1.]]),area,penalty);err=max(np.max(abs(r['u']-expected)),abs(r['pressure'][0]-P/area[0]),abs(r['multipliers'][0]));rows.append({'case':'mean_constrained_pair','error':float(err),'passed':bool(err<1e-10 and r['converged']),'history':r['history']})
report={'rows':rows,'passed':all(x['passed'] for x in rows),'joint_verified':False};(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));raise SystemExit(0 if report['passed'] else 1)
