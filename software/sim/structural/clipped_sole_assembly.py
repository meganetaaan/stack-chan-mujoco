"""Assemble affine-gap contact force/tangent over master/slave overlap triangles."""
import numpy as np
from scipy.sparse import coo_matrix
from bound_projected_contact_gap import clip,area,bary
from clipped_contact_triangle import integrate

def prepare(b,s):
    bx=b.p.T;sx=s.p.T;bt=b.facets[:,np.r_[b.boundaries['spacer_contact'],b.boundaries['contact_extension']]].T;st=s.facets[:,np.r_[s.boundaries['boss_contact'],s.boundaries['contact_extension']]].T
    master=bx[bt];lower=master[:,:,:2].min(axis=1);upper=master[:,:,:2].max(axis=1);patches=[];coverage=[]
    for ids in st:
        tri=sx[ids];lo=tri[:,:2].min(axis=0);hi=tri[:,:2].max(axis=0);candidates=np.flatnonzero(np.all(upper>=lo-1e-10,axis=1)&np.all(lower<=hi+1e-10,axis=1));covered=0.
        for j in candidates:
            poly=clip(list(tri[:,:2]),master[j,:,:2]);covered+=area(poly)
            if area(poly)<1e-14:continue
            dofs=np.r_[3*bt[j]+2,3*len(bx)+3*ids+2]
            for i in range(1,len(poly)-1):
                points=[poly[0],poly[i],poly[i+1]];ar=area(points)
                if ar<1e-18:continue
                G=np.array([np.r_[bary(q,master[j]),-bary(q,tri)] for q in points]);g0=G@np.r_[master[j,:,2],tri[:,2]]
                patches.append((dofs,G,g0,ar))
        coverage.append(abs(covered-area(list(tri[:,:2])))/area(list(tri[:,:2])))
    if max(coverage)>1e-8:raise ValueError('Incomplete overlap coverage')
    return patches,3*(len(bx)+len(sx)),{'patch_triangles':len(patches),'coverage_error':max(coverage)}

def assemble(patches,ndof,u,penalty=1e6):
    force=np.zeros(ndof);rows=[];cols=[];values=[];energy=0.;active_area=0.;peak=0.
    for dofs,G,g0,ar in patches:
        gap=g0+G@u[dofs];r=integrate(gap,ar,penalty);local=G.T@r['force'];np.add.at(force,dofs,local);kt=G.T@r['tangent']@G;rows.extend(np.repeat(dofs,6));cols.extend(np.tile(dofs,6));values.extend(kt.ravel());energy+=r['energy'];active_area+=r['active_area'];peak=max(peak,float(max(0,-gap.min())*penalty))
    tangent=coo_matrix((values,(rows,cols)),shape=(ndof,ndof)).tocsr();tangent.eliminate_zeros()
    return force,tangent,{'energy_Nmm':energy,'active_area_mm2':active_area,'peak_pressure_MPa':peak}

def equilibrate(K,C,F,patches,u,multipliers,penalty=1e6,max_iterations=20):
    """Newton correction from a nearby contact solution; fail visibly if not converged."""
    from scipy.sparse import bmat
    from scipy.sparse.linalg import spsolve
    u=u.copy();multipliers=multipliers.copy();history=[];converged=False
    for iteration in range(max_iterations):
        force,tangent,info=assemble(patches,len(F),u,penalty)
        residual=K@u-F-force+C.T@multipliers;constraint=C@u
        norm=float(np.linalg.norm(residual));cn=float(np.max(abs(constraint)))
        history.append({'iteration':iteration,'equilibrium_residual_N':norm,'constraint_residual':cn})
        A=bmat([[K+tangent,C.T],[C,None]],format='csc')
        if norm<=1e-7 and cn<=1e-8:converged=True;break
        if iteration==max_iterations-1:break
        step=spsolve(A,-np.r_[residual,constraint])
        if not np.isfinite(step).all():raise ValueError('Nonfinite Newton step')
        u+=step[:len(F)];multipliers+=step[len(F):]
    return u,multipliers,force,info,history,converged,A
