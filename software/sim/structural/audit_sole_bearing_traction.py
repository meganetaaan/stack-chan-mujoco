"""Inspect support tractions; distinguish P2 nodal forces from physical pressure."""
import argparse
import hashlib
import json
from pathlib import Path
import meshio
import numpy as np
from skfem import Basis, FacetBasis, ElementVector, ElementTetP2
from skfem.io import from_meshio
from skfem.models.elasticity import lame_parameters

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--source', type=Path, required=True)
p.add_argument('--mesh-file', type=Path)
p.add_argument('--fields-file', type=Path)
p.add_argument('--out', type=Path, required=True)
a = p.parse_args()
a.out.mkdir(parents=True, exist_ok=False)
plan = {
    'scope': 'Diagnostic of bilateral support solution; not unilateral contact verification',
    'young_MPa': 1120, 'poisson': .35,
    'pressure_convention': 'For bottom outward normal -z, upward support traction is -sigma_zz; positive is compressive',
    'tensile_detection_tolerance_MPa': 1e-6,
    'warning': 'Quadratic nodal reaction signs alone do not establish contact tension. Stress-derived boundary traction is approximate and not exactly equilibrated.',
}
(a.out/'plan.json').write_text(json.dumps(plan, indent=2)+'\n')
mesh_path = a.mesh_file or a.source/'boss_1.msh'
fields_path = a.fields_file or a.source/'probe_1mm.npz'
mesh = from_meshio(meshio.read(mesh_path))
element = ElementVector(ElementTetP2())
basis = Basis(mesh, element)
facets = mesh.boundaries['spacer_bearing']
face = FacetBasis(mesh, element, facets=facets)
fields = np.load(fields_path)
assert np.allclose(basis.doflocs[:, ::3].T, fields['nodes_mm'])
u = fields['displacement_mm'].reshape(-1)
grad = face.interpolate(u).grad
strain = (grad + grad.swapaxes(0, 1)) / 2
lam, mu = lame_parameters(plan['young_MPa'], plan['poisson'])
stress = 2*mu*strain + lam*np.einsum('iifq->fq', strain)[None,None]*np.eye(3)[:,:,None,None]
assert np.allclose(face.normals[2], -1)
traction = np.einsum('ijfq,jfq->ifq', stress, face.normals)
pressure = traction[2]
tensile = pressure < -plan['tensile_detection_tolerance_MPa']
zdofs = basis.get_dofs(facets=facets).all(['u^3'])
reaction = fields['reaction_N'].reshape(-1)[zdofs]
r = {
    'boundary_pressure_min_MPa': float(pressure.min()),
    'boundary_pressure_max_MPa': float(pressure.max()),
    'sampled_tensile_area_fraction': float(face.dx[tensile].sum()/face.dx.sum()),
    'stress_integrated_upward_traction_N': float(np.sum(pressure*face.dx)),
    'stress_integrated_tensile_magnitude_N': float(np.sum(np.maximum(-pressure, 0)*face.dx)),
    'assembled_support_upward_reaction_N': float(reaction.sum()),
    'negative_P2_nodal_reaction_count': int(np.sum(reaction < -1e-8)),
    'stress_traction_vs_reaction_relative_error': float(abs(np.sum(pressure*face.dx)-reaction.sum())/abs(reaction.sum())),
    'tension_detected_in_stress_samples': bool(tensile.any()),
    'unilateral_contact_verified': False,
    'source_sha256': {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in [mesh_path, fields_path]},
}
np.savez_compressed(a.out/'boundary_fields.npz',coordinates_mm=face.global_coordinates(),pressure_MPa=pressure,quadrature_area_mm2=face.dx)
(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps(r,indent=2))
