"""Small-displacement lumped normal penalty contact with linear gauge constraints."""
import numpy as np
from scipy.sparse import bmat,diags
from scipy.sparse.linalg import spsolve

def solve(K,C,F,B,area,penalty,initial_gap=None,max_iterations=80):
    F=np.asarray(F,dtype=float);area=np.asarray(area,dtype=float)
    gap0=np.zeros(len(area)) if initial_gap is None else np.asarray(initial_gap,dtype=float)
    if penalty<=0 or np.any(area<=0) or gap0.shape!=area.shape:
        raise ValueError('Positive penalty and areas, matching gap dimensions required')
    active=np.ones(len(area),dtype=bool);history=[];converged=False
    for iteration in range(max_iterations):
        d=penalty*area*active
        H=K+B.T@diags(d)@B
        A=bmat([[H,C.T],[C,None]],format='csc') if C.shape[0] else H.tocsc()
        rhs=np.r_[F-B.T@(d*gap0),np.zeros(C.shape[0])]
        solution=spsolve(A,rhs)
        if not np.isfinite(solution).all():raise ValueError('Nonfinite contact solution')
        u=solution[:len(F)];multipliers=solution[len(F):];gap=gap0+B@u;new_active=gap<0
        history.append({'iteration':iteration,'active_nodes':int(active.sum()),'changed_nodes':int(np.sum(active!=new_active))})
        if np.array_equal(active,new_active):converged=True;break
        active=new_active
    return {'u':u,'multipliers':multipliers,'gap':gap,'pressure':np.maximum(-penalty*gap,0),'converged':converged,'history':history,'matrix':A}
