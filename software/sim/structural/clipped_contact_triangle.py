"""Exact-degree integration of affine gap penalty on a clipped linear triangle."""
import numpy as np

def integrate(gap_vertices, projected_area, penalty=1.):
    g=np.asarray(gap_vertices,dtype=float)
    if g.shape!=(3,) or not np.isfinite(g).all() or projected_area<=0 or penalty<=0:raise ValueError('Finite gaps, positive area and penalty required')
    poly=list(np.eye(3));active=[];prev=poly[-1];gp=float(prev@g)
    for cur in poly:
        gc=float(cur@g)
        if (gp<0)!=(gc<0):active.append(prev+(cur-prev)*(gp/(gp-gc)))
        if gc<0:active.append(cur)
        prev=cur;gp=gc
    mass=np.zeros((3,3));active_area=0.
    q=np.array([[2/3,1/6,1/6],[1/6,2/3,1/6],[1/6,1/6,2/3]])
    for i in range(1,len(active)-1):
        t=np.array([active[0],active[i],active[i+1]])
        # Reference barycentric (lambda1,lambda2) triangle has area 1/2.
        area=projected_area*abs(np.linalg.det(t[1:,1:]-t[0,1:]));active_area+=area
        for w in q:
            N=w@t;mass+=area/3*np.outer(N,N)
    return {'force':-penalty*mass@g,'tangent':penalty*mass,'energy':float(.5*penalty*g@mass@g),'active_area':float(active_area)}
