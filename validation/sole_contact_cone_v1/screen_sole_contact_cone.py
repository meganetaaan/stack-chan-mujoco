"""Discrete compression/friction feasibility at the sole-yoke interface; not pressure FE."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from scipy.optimize import linprog
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();root=Path(__file__).resolve().parents[3];a.out.mkdir(parents=True,exist_ok=False)
plan={'scope':__doc__,'grid_mm':4,'friction_trials':[0,.1,.2,.4,.8,1.6],'criteria':{'wrench_residual':1e-6,'minimum_normal_force_N':-1e-8},'limitations':['Finite support points, no pressure/deflection or strength calculation.','Diamond friction pyramid |Fx|+|Fy|<=mu*Fz is inside circular Coulomb cone.','Floor resultant transferred across sole without sole inertia; only a diagnostic.','Selected maximum moment sample per foot/trace; not all-time proof.','Friction trials are assumptions, not material specifications.']};(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');rows=[]
for inset in [25.8,25.95]:
 src=root/f'validation/rounded_sole_load_audit_v1/local{inset}/wrenches.npz'
 with np.load(src) as d:allw=d['wrench_N_Nmm'];times=d['time_s']
 for foot,side in enumerate(['left','right']):
  cy=6 if side=='left' else -6;center=np.array([1,cy,-19]);points=[]
  # Interior grid plus finely sampled outer rounded boundary; head pockets excluded.
  for x in np.linspace(-39,47,23):
   for y in np.linspace(cy-24,cy+24,13):
    if np.hypot(max(abs(x-4)-40,0),max(abs(y-cy)-21,0))<=3+1e-9:points.append([x,y,-19])
  for x,y,start in [(44,cy+21,0),(-36,cy+21,90),(-36,cy-21,180),(44,cy-21,270)]:
   for t in np.linspace(start,start+90,17):points.append([x+3*np.cos(np.deg2rad(t)),y+3*np.sin(np.deg2rad(t)),-19])
  points=np.unique(np.round(points,10),axis=0);points=np.array([q for q in points if all(np.hypot(q[0]-x,q[1]-y)>=2.4 for x in [-34,36] for y in [cy-20.5,cy+20.5])]);n=len(points)
  A=np.zeros((6,3*n))
  for j,r in enumerate(points-center):
   x,y,z=r;A[:3,3*j:3*j+3]=np.eye(3);A[3:,3*j:3*j+3]=[[0,-z,y],[z,0,-x],[-y,x,0]]
  idx=int(np.linalg.norm(allw[:,foot,3:],axis=1).argmax());w=allw[idx,foot];trials=[]
  for mu in plan['friction_trials']:
   U=np.zeros((4*n,3*n))
   for j in range(n):
    for k,(sx,sy) in enumerate([(1,1),(1,-1),(-1,1),(-1,-1)]):U[4*j+k,3*j:3*j+3]=[sx,sy,-mu]
   res=linprog(np.tile([0,0,1.],n),A_ub=U,b_ub=np.zeros(4*n),A_eq=A,b_eq=w,bounds=[v for j in range(n) for v in [(None,None),(None,None),(0,None)]],method='highs');entry={'mu':mu,'solver_status':int(res.status),'feasible':bool(res.success)}
   if res.success:
    f=res.x.reshape(n,3);error=float(abs(A@res.x-w).max());entry.update(maximum_wrench_residual=error,active_points=int((f[:,2]>1e-8).sum()));assert error<1e-6 and f[:,2].min()>=-1e-8;np.savez_compressed(a.out/f'inset{inset}_{side}_mu{mu}.npz',points_mm=points,force_N=f,wrench_N_Nmm=w)
   trials.append(entry)
  rows.append({'inset_mm':inset,'side':side,'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'sample_index':idx,'time_s':float(times[idx]),'wrench_N_Nmm':w.tolist(),'support_points':n,'trials':trials})
r={'cases':rows,'joint_verified':False};(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps([{'inset':r['inset_mm'],'side':r['side'],'feasible_mu':[t['mu'] for t in r['trials'] if t['feasible']]} for r in rows],indent=2))
