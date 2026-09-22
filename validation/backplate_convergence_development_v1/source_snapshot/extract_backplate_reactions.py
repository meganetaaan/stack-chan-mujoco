"""Export corner resultants from an ideal-clamped plate FE solution, not screw loads."""
import argparse, hashlib, json
from pathlib import Path
import meshio
import numpy as np
from skfem import Basis, ElementVector, ElementTetP2
from skfem.io import from_meshio

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--analysis', type=Path, required=True)
p.add_argument('--out', type=Path, required=True)
a = p.parse_args()
a.out.mkdir(parents=True, exist_ok=False)
plan = json.loads((a.analysis/'plan.json').read_text())
mesh = from_meshio(meshio.read(a.analysis/'cover.msh'))
basis = Basis(mesh, ElementVector(ElementTetP2()))
centers = np.array([[-62.2,y,z] for y in [-59,59] for z in [8,120]])
def fixed(x):
    return (abs(x[0]+62.2)<1e-6) & np.any(
        ((x[1,None,:]-centers[:,1,None])**2 +
         (x[2,None,:]-centers[:,2,None])**2)<=4.6**2, axis=0)
facets = mesh.facets_satisfying(fixed, boundaries_only=True)
nodes = np.unique(basis.get_dofs(facets=facets).all()//3)
rows = []
for name in ['left_only','right_only','simultaneous']:
    with np.load(a.analysis/(name+'.npz')) as data:
        xyz = data['nodes_mm']; reaction = data['reaction_N']; applied = data['load_N']
        assert np.allclose(xyz,basis.doflocs[:,::3].T,atol=1e-10,rtol=0)
        assert np.max(abs(data['displacement_mm'][nodes]))<1e-12
        nearest = np.argmin(np.linalg.norm(xyz[nodes,None,:]-centers[None,:,:],axis=2),axis=1)
        corners = []
        for i, center in enumerate(centers):
            ix = nodes[nearest==i]
            assert len(ix)>0 and np.max(np.linalg.norm(xyz[ix]-center,axis=1))<7
            wrench = np.r_[reaction[ix].sum(axis=0),np.cross(xyz[ix]-center,reaction[ix]).sum(axis=0)]
            corners.append({'origin_mm':center.tolist(),'fixed_node_count':len(ix),
                            'reaction_on_plate_N_Nmm':wrench.tolist(),
                            'load_on_body_N_Nmm':(-wrench).tolist()})
        balance = np.r_[reaction[nodes].sum(axis=0)+applied.sum(axis=0),
                        np.cross(xyz[nodes],reaction[nodes]).sum(axis=0)+np.cross(xyz,applied).sum(axis=0)]
        assert np.max(abs(balance))<1e-5, balance
        rows.append({'case':name,'corners':corners,'global_equilibrium_residual_N_Nmm':balance.tolist()})
report = {'scope':__doc__,'rows':rows,
          'sources_sha256':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in a.analysis.iterdir() if f.is_file()},
          'limitations':['single recorded load time','ideal clamps can transmit moments that a screw joint cannot without contact',
                         'rigid-support load sharing changes with compliant body and fasteners',
                         'resultants are input candidates for coupled analysis, not verified individual screw forces'],
          'joint_verified':False}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'cases':len(rows),'max_equilibrium_residual':max(max(abs(v) for v in r['global_equilibrium_residual_N_Nmm']) for r in rows)}))
