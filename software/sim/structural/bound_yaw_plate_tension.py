"""Normal tensile-transfer lower bounds over archived yaw load histories."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from scipy.optimize import linprog
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
base=Path('validation/yaw_connection_development_v1/bolt_group_v1');index=base/'report.json';cases=json.loads(index.read_text())['rows']
plan={'question':'Does one selected case cover tensile transfer required by archived normal force and bending histories?',
 'sources':'All 38 cases listed in bolt_group_v1/report.json, including development variants; fullbody subset identified separately.',
 'index_sha256':hashlib.sha256(index.read_bytes()).hexdigest(),
 'geometry':'Contact rectangle X[-37.5,11.6], Y=cy+/-16.5 at Z89. Bolt axes X[-34,8.1], Y=cy+/-10.',
 'method':'Rigid normal force/moment balance. Total T>=0, C=Fz+T>=0. Contact and bolt point sets span independent XY rectangles. Bound each first moment by their Minkowski rectangle; maximum of the five inequalities and zero is exact for this relaxed model.',
 'stop':'One vectorized pass over indexed traces; LP equilibrium check at maximum bound, minimum Fz and maximum Fz per case. No FE or unknown-parameter sweep.',
 'limits':['Lower bound, not required preload or maximum individual bolt load','Contact rectangle fills holes and cutout, so is optimistic','Ignores shear, torsion, friction, flexibility, preload and dynamics internal to joint','Archived development loads are not the latest complete operating envelope','No strength or manufacturing release']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');rows=[];hashes={}
xc=np.array([-37.5,11.6])-(-12.95);xt=np.array([-34,8.1])-(-12.95)
corners=np.array([[x,y] for x in xc for y in [-16.5,16.5]])
bolts=np.array([[x,y] for x in xt for y in [-10,10]])
def columns(x):return np.vstack([np.ones(4),x[:,1],-x[:,0]])
A=np.hstack([columns(corners),-columns(bolts)])
for case in cases:
 path=base/(Path(case['source']).parent.name+'_'+case['side']+'.npz');hashes[str(path)]=hashlib.sha256(path.read_bytes()).hexdigest()
 with np.load(path) as d:t=d['time_s'];w=d['wrench_at_bolt_group_N_Nmm'].copy()
 # Reference displacement from plate centre to archived rear bolt-group centre.
 shift=np.array([-60,0,70])-np.array([-12.95,0,89]);w[:,3:]+=np.cross(shift,w[:,:3])
 F=w[:,2];Nx=-w[:,4];Ny=w[:,3]
 terms=np.array([np.zeros(len(F)),-F,(Nx-xc[1]*F)/(xc[1]-xt[0]),(xc[0]*F-Nx)/(xt[1]-xc[0]),(Ny-16.5*F)/26.5,(-16.5*F-Ny)/26.5])
 bound=terms.max(axis=0);peak=int(bound.argmax());checks=[]
 for i in sorted(set([peak,int(F.argmin()),int(F.argmax())])):
  target=w[i,[2,3,4]];lp=linprog(np.r_[np.zeros(4),np.ones(4)],A_eq=A,b_eq=target,bounds=(0,None),method='highs')
  assert lp.success and np.allclose(A@lp.x,target,atol=1e-7) and np.isclose(lp.fun,bound[i],atol=1e-7)
  checks.append({'sample':i,'lp_total_tension_N':float(lp.fun)})
 rows.append({'source':case['source'],'side':case['side'],'samples':len(t),'fullbody_case':'actuator_fullbody_load_' in case['source'],'samples_requiring_tension':int((bound>1e-7).sum()),'maximum_total_tension_lower_bound_N':float(bound[peak]),'peak_time_s':float(t[peak]),'peak_wrench_at_plate_centre_N_Nmm':w[peak].tolist(),'active_bound_index':int(terms[:,peak].argmax()),'lp_cross_checks':checks})
 np.savez_compressed(a.out/(path.stem+'_tension.npz'),time_s=t,total_tension_lower_bound_N=bound)
full=[x for x in rows if x['fullbody_case']]
result={'source_sha256':hashes,'rows':rows,'total_samples':sum(x['samples'] for x in rows),'max_case':max(rows,key=lambda x:x['maximum_total_tension_lower_bound_N']),'max_fullbody_case':max(full,key=lambda x:x['maximum_total_tension_lower_bound_N']),'manufacturing_release':False}
(a.out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['total_samples','max_case','max_fullbody_case']},indent=2))
