"""Quadratic tetrahedral linear elasticity with resultant-preserving face loads.

Units: mm, N, MPa. This is a bonded/clamped component solver, not a contact or
buckling solver. Boundary selections and geometry must be justified per case.
"""
from pathlib import Path
import gmsh
import meshio
import numpy as np
from skfem import Basis, FacetBasis, ElementVector, ElementTetP2, LinearForm, asm
from skfem.io import from_meshio
from skfem.models.elasticity import linear_elasticity, lame_parameters
from scipy.sparse.linalg import splu


def tetrahedralize(step, out, size):
    gmsh.initialize()
    try:
        gmsh.option.setNumber('General.Terminal', 0)
        gmsh.model.occ.importShapes(str(step))
        gmsh.model.occ.synchronize()
        gmsh.option.setNumber('Mesh.MeshSizeMin', size)
        gmsh.option.setNumber('Mesh.MeshSizeMax', size)
        gmsh.option.setNumber('Mesh.Algorithm3D', 1)
        gmsh.model.mesh.generate(3)
        gmsh.write(str(out))
    finally:
        gmsh.finalize()
    return from_meshio(meshio.read(out))


def skew(r):
    x, y, z = r
    return np.array([[0, -z, y], [z, 0, -x], [-y, x, 0]])


def select_boundary(mesh, selector):
    """Resolve a callable or a CAD physical-group name to boundary facets."""
    if callable(selector):
        return mesh.facets_satisfying(selector, boundaries_only=True)
    if not isinstance(selector, str) or not mesh.boundaries or selector not in mesh.boundaries:
        raise ValueError('Unknown boundary physical group')
    facets = np.asarray(mesh.boundaries[selector], dtype=int)
    if not set(facets).issubset(set(mesh.boundary_facets())):
        raise ValueError('Physical group contains internal facets')
    return facets


def analyze_regions_many(mesh, fixed_selector, regions, load_cases, young=1400., poisson=.35):
    """Solve cases of independent six-component loads on disjoint face regions."""
    element = ElementVector(ElementTetP2())
    basis = Basis(mesh, element)
    fixed = select_boundary(mesh, fixed_selector)
    if not len(fixed):
        raise ValueError('Empty support surface')
    region_data = []
    occupied = set(fixed)
    for selector, origin in regions:
        loaded = select_boundary(mesh, selector)
        if not len(loaded) or occupied.intersection(loaded):
            raise ValueError('Empty or overlapping load region')
        occupied.update(loaded)
        face = FacetBasis(mesh, element, facets=loaded)
        origin = np.asarray(origin, dtype=float)
        coords = face.global_coordinates()
        resultant_map = np.zeros((6, 6))
        for f in range(coords.shape[1]):
            for q in range(coords.shape[2]):
                r = coords[:, f, q] - origin
                B = np.hstack((np.eye(3), -skew(r)))
                A = np.vstack((np.eye(3), skew(r)))
                resultant_map += A @ B * face.dx[f, q]
        if np.linalg.matrix_rank(resultant_map) != 6:
            raise ValueError('Load surface cannot represent all resultant components')
        region_data.append((face, origin, resultant_map, len(loaded)))
    if not region_data:
        raise ValueError('At least one load region is required')
    reference_origin = region_data[0][1]
    locations = basis.doflocs[:, ::3].T
    lam, mu = lame_parameters(young, poisson)
    stiffness = asm(linear_elasticity(lam,mu), basis)
    constrained = basis.get_dofs(facets=fixed).all()
    free = np.setdiff1d(np.arange(basis.N),constrained)
    factor = splu(stiffness[free][:,free].tocsc())
    for wrenches in load_cases:
        wrenches = np.asarray(wrenches, dtype=float)
        if wrenches.shape != (len(region_data), 6) or not np.isfinite(wrenches).all():
            raise ValueError('Each load case must have one finite six-component wrench per region')
        load = np.zeros(basis.N)
        region_reports = []
        expected = np.zeros(6)
        for wrench, (face, origin, resultant_map, count) in zip(wrenches, region_data):
            coefficients = np.linalg.solve(resultant_map, wrench)

            @LinearForm
            def traction(v, w):
                r = w.x - origin[:, None, None]
                force = coefficients[:3, None, None] + np.cross(coefficients[3:], np.moveaxis(r, 0, -1)).transpose(2, 0, 1)
                return np.einsum('i...,i...->...', force, v)

            region_load = asm(traction, face)
            force = region_load.reshape(-1, 3)
            achieved_region = np.r_[force.sum(axis=0), np.cross(locations-origin, force).sum(axis=0)]
            if not np.allclose(achieved_region, wrench, atol=1e-7, rtol=1e-8):
                raise ValueError('Region assembly lost force or moment')
            load += region_load
            expected[:3] += wrench[:3]
            expected[3:] += wrench[3:] + np.cross(origin-reference_origin, wrench[:3])
            region_reports.append({'origin_mm':origin.tolist(), 'facets':count,
                                   'achieved_wrench_N_Nmm':achieved_region.tolist()})
        displacement = np.zeros(basis.N)
        displacement[free] = factor.solve(load[free])
        residual = stiffness@displacement-load
        nodal_f = load.reshape(-1,3)
        locations = basis.doflocs[:,::3].T
        achieved = np.r_[nodal_f.sum(axis=0),np.cross(locations-reference_origin,nodal_f).sum(axis=0)]
        if not np.allclose(achieved,expected,atol=1e-7,rtol=1e-8):
            raise ValueError('Assembled load lost the requested force or moment')
        gradient = basis.interpolate(displacement).grad
        strain = (gradient+gradient.swapaxes(0,1))*.5
        stress = 2*mu*strain+lam*np.einsum('iieq->eq',strain)[None,None,:,:]*np.eye(3)[:,:,None,None]
        stress_matrices = np.moveaxis(stress,(0,1),(-2,-1))
        principals = np.linalg.eigvalsh(stress_matrices)
        von_mises = np.sqrt(((principals[...,0]-principals[...,1])**2+
                             (principals[...,1]-principals[...,2])**2+
                             (principals[...,2]-principals[...,0])**2)/2)
        report = {'dofs':int(basis.N),'elements':int(mesh.nelements),'fixed_facets':len(fixed),'loaded_facets':sum(r[3] for r in region_data),'load_regions':region_reports,
                  'max_displacement_mm':float(np.linalg.norm(displacement.reshape(-1,3),axis=1).max()),
                  'max_von_mises_MPa':float(von_mises.max()),
                  'max_absolute_principal_MPa':float(abs(principals).max()),
                  'achieved_wrench_N_Nmm':achieved.tolist(),
                  'free_residual_norm_N':float(np.linalg.norm(residual[free])),
                  'strain_energy_Nmm':float(displacement@stiffness@displacement*.5),
                  'external_work_Nmm':float(displacement@load),
                  'stress_evaluation':'all integration points, no excluded corner or support singularities'}
        arrays={'nodes_mm':locations,'displacement_mm':displacement.reshape(-1,3),
                'quadrature_coordinates_mm':basis.global_coordinates(),'stress_MPa':stress,
                'load_N':nodal_f,'reaction_N':residual.reshape(-1,3)}
        yield report, arrays


def analyze_many(mesh, fixed_selector, loaded_selector, origin, wrenches, young=1400., poisson=.35):
    """Compatibility wrapper for one loaded surface region."""
    yield from analyze_regions_many(mesh, fixed_selector, [(loaded_selector, origin)],
                                    (np.asarray(w)[None, :] for w in wrenches), young, poisson)


def analyze(mesh, fixed_selector, loaded_selector, origin, wrench, young=1400., poisson=.35):
    """Single-load wrapper retaining the original public interface."""
    return next(analyze_many(mesh, fixed_selector, loaded_selector, origin, [wrench], young, poisson))
