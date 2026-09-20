"""Partition current rear-joint solids by audited contact patches and mesh them."""
import argparse, hashlib, json
from pathlib import Path
import gmsh
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--out', type=Path, required=True)
p.add_argument('--mesh-mm', type=float, default=3.)
p.add_argument('--include-hardware', action='store_true')
a = p.parse_args()
assert np.isfinite(a.mesh_mm) and a.mesh_mm > 0
a.out.mkdir(parents=True, exist_ok=False)
audit = ROOT/'validation/rear_contact_geometry_development_v1/audit_v1'
report = json.loads((audit/'report.json').read_text())
config = json.loads((ROOT/'board/mechanical/engineering/rear_connection_candidate.json').read_text())
assets = dict(config['assets'])
if a.include_hardware:
    hashes = json.loads((audit/'plan.json').read_text())['source_sha256']
    for i in range(4):
        for kind in ['bolt', 'nut', 'inner_washer', 'rear_washer']:
            matches = [name for name in hashes if name.endswith(f'/corner_{i}_{kind}.step')]
            assert len(matches) == 1
            assets[f'{kind}_{i}'] = {'path': matches[0], 'sha256': hashes[matches[0]]}
plan = {'scope': __doc__, 'parts': list(assets), 'mesh_mm': a.mesh_mm,
        'criteria': {'relative_contact_area_error': .01, 'relative_volume_change': 1e-8},
        'limitations': ['mesh preparation only; no contact or preload solve', 'linear tetrahedral geometry',
                        'thread envelopes remain nonphysical; no thread connector included'],
        'audit_sha256': hashlib.sha256((audit/'report.json').read_bytes()).hexdigest(),
        'assets': assets}
(a.out/'plan.json').write_text(json.dumps(plan, indent=2)+'\n')
rows = []
for part in plan['parts']:
    source = ROOT/assets[part]['path']
    assert hashlib.sha256(source.read_bytes()).hexdigest() == assets[part]['sha256']
    contacts = [c for c in report['contacts'] if part in c['parts']]
    gmsh.initialize()
    try:
        gmsh.option.setNumber('General.Terminal', 0)
        volumes = [v for v in gmsh.model.occ.importShapes(str(source)) if v[0] == 3]
        assert len(volumes) == 1
        before = gmsh.model.occ.getMass(*volumes[0])
        surfaces = []; owners = []
        for c in contacts:
            faces = [v for v in gmsh.model.occ.importShapes(str(audit/(c['name']+'.step'))) if v[0] == 2]
            assert faces
            surfaces.extend(faces); owners.extend([c['name']]*len(faces))
        _, mapping = gmsh.model.occ.fragment(volumes, surfaces)
        gmsh.model.occ.synchronize()
        volumes = gmsh.model.getEntities(3)
        assert len(volumes) == 1
        after = gmsh.model.occ.getMass(*volumes[0])
        assert abs(after-before)/before < plan['criteria']['relative_volume_change']
        boundary = {t for d,t in gmsh.model.getBoundary(volumes, oriented=False) if d == 2}
        groups = {c['name']: set() for c in contacts}
        for name, mapped in zip(owners, mapping[1:]):
            groups[name].update(t for d,t in mapped if d == 2 and t in boundary)
        used = [t for tags in groups.values() for t in tags]
        assert len(used) == len(set(used)), 'Overlapping contact groups'
        for name,tags in groups.items():
            assert tags, name
            g = gmsh.model.addPhysicalGroup(2, sorted(tags)); gmsh.model.setPhysicalName(2,g,name)
        g = gmsh.model.addPhysicalGroup(3,[t for _,t in volumes]); gmsh.model.setPhysicalName(3,g,part)
        stray = [(2,t) for _,t in gmsh.model.getEntities(2) if t not in boundary]
        if stray: gmsh.model.occ.remove(stray,recursive=False)
        gmsh.model.occ.synchronize()
        gmsh.write(str(a.out/(part+'.brep')))
        gmsh.option.setNumber('Mesh.MeshSizeMin',a.mesh_mm)
        gmsh.option.setNumber('Mesh.MeshSizeMax',a.mesh_mm)
        gmsh.option.setNumber('Mesh.MinimumCirclePoints',32)
        gmsh.option.setNumber('Mesh.MeshSizeExtendFromBoundary',0)
        gmsh.model.mesh.generate(3)
        gmsh.option.setNumber('Mesh.MshFileVersion',2.2)
        gmsh.write(str(a.out/(part+'.msh')))
        ids, xyz, _ = gmsh.model.mesh.getNodes()
        coords = dict(zip(ids, np.asarray(xyz).reshape(-1,3)))
        checks = []
        for c in contacts:
            tags = groups[c['name']]
            cad_area = sum(gmsh.model.occ.getMass(2,t) for t in tags)
            assert abs(cad_area-c['area_mm2']) < 1e-5
            area = 0.; count = 0
            for t in tags:
                types, element_ids, nodes = gmsh.model.mesh.getElements(2,t)
                for typ, ei, ns in zip(types, element_ids, nodes):
                    assert typ == 2
                    points = np.array([coords[n] for n in ns]).reshape(-1,3,3)
                    area += np.linalg.norm(np.cross(points[:,1]-points[:,0],points[:,2]-points[:,0]),axis=1).sum()/2
                    count += len(ei)
            error = abs(area-cad_area)/cad_area
            checks.append({'name':c['name'],'faces':sorted(tags),'triangles':count,'cad_area_mm2':cad_area,
                           'mesh_area_mm2':float(area),'relative_error':float(error),'passed':bool(error<.01)})
        row = {'part':part,'volume_before_mm3':before,'volume_after_mm3':after,'contacts':checks,
               'nodes':len(ids),'passed':all(c['passed'] for c in checks)}
        rows.append(row)
        (a.out/(part+'.json')).write_text(json.dumps(row,indent=2)+'\n')
        print(json.dumps(row),flush=True)
    finally:
        gmsh.finalize()
(a.out/'report.json').write_text(json.dumps({'parts':rows,'passed':all(r['passed'] for r in rows),
    'strength_verified':False,'preload_verified':False},indent=2)+'\n')
