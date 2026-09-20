"""Conformal CAD partition of rear-plate mounting and loaded annuli (mm)."""
import argparse,json,hashlib
from pathlib import Path
import gmsh,meshio,numpy as np
from skfem.io import from_meshio

def build_mesh(step,out,size,circle_points=32):
    if not np.isfinite(size) or size<=0 or circle_points<32:
        raise ValueError("Positive finite mesh size and at least 32 circle points required")
    out=Path(out)
    if any(f.exists() for f in [out,out.with_suffix('.brep'),out.with_suffix('.patches.json')]):
        raise FileExistsError('Refusing to overwrite existing mesh evidence')
    gmsh.initialize()
    try:
        gmsh.option.setNumber('General.Terminal',0)
        volumes=gmsh.model.occ.importShapes(str(step))
        volumes=[dt for dt in volumes if dt[0]==3]
        assert len(volumes)==1
        volume_before=gmsh.model.occ.getMass(*volumes[0])
        patches=[]
        for name,centers,radius,hole in [
            ('fixed',[(y,z) for y in [-59,59] for z in [8,120]],4.6,1.65),
            ('left',[(26+dy,70+dz) for dy in [-7,7] for dz in [-12,12]],6.,1.7),
            ('right',[(-26+dy,70+dz) for dy in [-7,7] for dz in [-12,12]],6.,1.7)]:
            for y,z in centers:
                tag=gmsh.model.occ.addDisk(-62.2,y,z,radius,radius,zAxis=[1,0,0])
                patches.append((name,tag,np.pi*(radius**2-hole**2)))
        _,mapping=gmsh.model.occ.fragment(volumes,[(2,t) for _,t,_ in patches])
        gmsh.model.occ.synchronize()
        volumes=gmsh.model.getEntities(3);assert len(volumes)==1
        volume_after=gmsh.model.occ.getMass(*volumes[0])
        assert abs(volume_after-volume_before)<1e-6
        boundary={abs(t) for d,t in gmsh.model.getBoundary(volumes,oriented=False) if d==2}
        grouped={n:[] for n in ['fixed','left','right']};rows=[]
        for (name,tag,expected),mapped in zip(patches,mapping[1:]):
            faces=[t for d,t in mapped if d==2 and t in boundary]
            area=sum(gmsh.model.occ.getMass(2,t) for t in faces)
            assert faces and abs(area-expected)<1e-6,(name,area,expected)
            grouped[name].extend(faces);rows.append({'group':name,'faces':faces,'area_mm2':area,'expected_area_mm2':expected})
        used=[t for group in grouped.values() for t in group];assert len(used)==len(set(used))
        for name,tags in grouped.items():
            g=gmsh.model.addPhysicalGroup(2,tags);gmsh.model.setPhysicalName(2,g,name)
        g=gmsh.model.addPhysicalGroup(3,[t for _,t in volumes]);gmsh.model.setPhysicalName(3,g,'plate')
        # Unattached disk pieces inside the through-holes must not become load faces.
        stray=[(2,t) for _,t in gmsh.model.getEntities(2) if t not in boundary]
        gmsh.model.occ.remove(stray,recursive=False);gmsh.model.occ.synchronize()
        gmsh.write(str(out.with_suffix('.brep')))
        gmsh.option.setNumber('Mesh.MeshSizeMin',size)
        gmsh.option.setNumber('Mesh.MeshSizeMax',size)
        gmsh.option.setNumber('Mesh.MinimumCirclePoints',circle_points)
        # Keep local circular-edge resolution from propagating across the whole plate.
        gmsh.option.setNumber('Mesh.MeshSizeExtendFromBoundary',0)
        gmsh.option.setNumber('Mesh.Algorithm3D',1)
        gmsh.model.mesh.generate(3)
        gmsh.option.setNumber('Mesh.MshFileVersion',2.2)
        gmsh.write(str(out))
    finally:gmsh.finalize()
    mesh=from_meshio(meshio.read(out))
    checks={}
    for name in grouped:
        facets=mesh.boundaries[name]
        assert len(facets)>0 and set(facets).issubset(set(mesh.boundary_facets()))
        p=mesh.p[:,mesh.facets[:,facets]]
        area=float(np.linalg.norm(np.cross((p[:,1]-p[:,0]).T,(p[:,2]-p[:,0]).T),axis=1).sum()/2)
        cad_area=sum(r['area_mm2'] for r in rows if r['group']==name)
        checks[name]={'facets':len(facets),'mesh_area_mm2':area,'cad_area_mm2':cad_area,'relative_area_error':abs(area-cad_area)/cad_area}
        assert checks[name]['relative_area_error']<.01
    report={'source_sha256':hashlib.sha256(Path(step).read_bytes()).hexdigest(),'mesh_mm':size,'circle_points':circle_points,'extend_boundary_sizes':False,
            'volume_before_mm3':volume_before,'volume_after_mm3':volume_after,'patches':rows,'mesh_checks':checks,
            'elements':mesh.nelements,'criteria':{'relative_patch_area_error':.01},
            'limitations':['linear chord geometry approximates circular boundaries','ideal fixed annuli; not contact analysis']}
    out.with_suffix('.patches.json').write_text(json.dumps(report,indent=2)+'\n')
    return mesh

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--step',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--mesh-mm',type=float,default=3.);p.add_argument('--circle-points',type=int,default=32)
    a=p.parse_args();a.out.parent.mkdir(parents=True,exist_ok=True);build_mesh(a.step,a.out,a.mesh_mm,a.circle_points)
