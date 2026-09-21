"""Initial-normal contact quadrature projected onto the planar boss underside."""
import argparse,json
from pathlib import Path
import meshio,numpy as np
from scipy.sparse import csr_matrix,save_npz
from skfem.io import from_meshio

def project(boss,spacer):
    bm=boss.p.T;sm=spacer.p.T
    master=boss.facets[:,np.r_[boss.boundaries['spacer_contact'],boss.boundaries['contact_extension']]].T
    slave=spacer.facets[:,np.r_[spacer.boundaries['boss_contact'],spacer.boundaries['contact_extension']]].T
    assert np.allclose(bm[master,2],-19,atol=1e-8)
    mt=bm[master,:2];mat=np.stack([mt[:,1]-mt[:,0],mt[:,2]-mt[:,0]],axis=2);inv=np.linalg.inv(mat)
    qweights=np.array([[2/3,1/6,1/6],[1/6,2/3,1/6],[1/6,1/6,2/3]])
    rows=[];cols=[];vals=[];gaps=[];areas=[];positions=[];err=[];mom=[];offset=3*len(bm)
    for tri in slave:
        x=sm[tri];delta=x[1:,:2]-x[0,:2];area=abs(np.linalg.det(delta))/2
        if area<=1e-14:raise ValueError('Degenerate projected contact triangle')
        for sw in qweights:
            q=sw@x;uv=np.einsum('nij,nj->ni',inv,q[:2]-mt[:,0]);bw=np.c_[1-uv.sum(axis=1),uv];hits=np.flatnonzero(np.min(bw,axis=1)>=-1e-9)
            if not len(hits):raise ValueError('Slave point outside master triangulation')
            j=int(hits[0]);w=bw[j];target=w@bm[master[j]];gap=target[2]-q[2]
            if gap < -1e-8:raise ValueError('Initial penetration')
            row=len(gaps)
            for n,v in zip(master[j],w):rows.append(row);cols.append(3*int(n)+2);vals.append(float(v))
            for n,v in zip(tri,sw):rows.append(row);cols.append(offset+3*int(n)+2);vals.append(float(-v))
            gaps.append(max(0,gap));areas.append(area/3);positions.append(q);err.append(max(abs(w.sum()-1),np.max(abs(target[:2]-q[:2]))));mom.append(np.linalg.norm(np.cross(target-q,[0,0,1])))
    B=csr_matrix((vals,(rows,cols)),shape=(len(gaps),3*(len(bm)+len(sm))))
    r={'quadrature_points':len(gaps),'projected_area_mm2':float(sum(areas)),'initial_gap_min_mm':float(min(gaps)),'initial_gap_max_mm':float(max(gaps)),'positive_gap_points':int(np.sum(np.array(gaps)>1e-8)),'maximum_partition_or_xy_error':float(max(err)),'maximum_unit_force_moment_imbalance_mm':float(max(mom)),'maximum_unit_force_imbalance':float(abs(np.asarray(B.sum(axis=1))).max()),'scope':'Three points per slave triangle, projected area and initial vertical normals; no finite sliding or contact solve'}
    assert max(err)<1e-8 and max(mom)<1e-8
    return B,np.array(areas),np.array(gaps),np.array(positions),r

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--mesh-dir',type=Path,required=True);p.add_argument('--mesh-mm',default='0.5');p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    (a.out/'plan.json').write_text(json.dumps({'scope':__doc__,'coordinate_and_force_tolerance':1e-8,'initial_penetration_tolerance_mm':1e-8,'joint_verified':False},indent=2)+'\n')
    ms=[from_meshio(meshio.read(a.mesh_dir/n/f'{n}_{a.mesh_mm}.msh')) for n in ['boss','spacer']];B,area,gap,x,r=project(*ms);save_npz(a.out/'gap_operator.npz',B);np.savez_compressed(a.out/'quadrature.npz',area_mm2=area,initial_gap_mm=gap,positions_mm=x);(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
