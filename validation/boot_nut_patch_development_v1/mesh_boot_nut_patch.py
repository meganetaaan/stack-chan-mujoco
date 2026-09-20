"""Imprint actual nominal nut footprint on a local seat for contact/traction meshing."""
import argparse,json,hashlib,math
from pathlib import Path
import gmsh,meshio,numpy as np
from skfem.io import from_meshio
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[3]
if a.out.exists():p.error('new output required')
a.out.mkdir(parents=True)
source=root/'validation/boot_nut_seat_fe_development_v1/local_seat.step';expected=16-math.pi*1.15**2
plan={'scope':__doc__,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'nut_patch_xy_mm':{'x':[-36,-32],'y':[-16.5,-12.5]},'patch_z_mm':-14.6,'expected_patch_area_mm2':expected,'mesh_mm':[1,.7,.5],'criteria':{'cad_area_error_mm2':1e-6,'mesh_area_relative_error':.01,'volume_change_mm3':1e-6},'limitations':['Surface partition only; not a unilateral contact solve.','Nominal square nut face with circular through-hole; no nut edge chamfer.']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');rows=[]
for size in plan['mesh_mm']:
 gmsh.initialize()
 try:
  gmsh.option.setNumber('General.Terminal',0)
  volumes=[v for v in gmsh.model.occ.importShapes(str(source)) if v[0]==3]
  before=sum(gmsh.model.occ.getMass(*v) for v in volumes)
  patch=gmsh.model.occ.addRectangle(-36,-16.5,-14.6,4,4)
  _,mapping=gmsh.model.occ.fragment(volumes,[(2,patch)]);gmsh.model.occ.synchronize()
  vols=gmsh.model.getEntities(3);boundary={t for d,t in gmsh.model.getBoundary(vols,oriented=False) if d==2}
  faces=[t for d,t in mapping[-1] if d==2 and t in boundary]
  area=sum(gmsh.model.occ.getMass(2,t) for t in faces)
  after=sum(gmsh.model.occ.getMass(*v) for v in vols)
  if len(vols)!=1 or abs(after-before)>1e-6 or abs(area-expected)>1e-6:raise ValueError('CAD partition check failed')
  g=gmsh.model.addPhysicalGroup(2,faces);gmsh.model.setPhysicalName(2,g,'nut_bearing')
  bottom=[t for t in boundary if abs(gmsh.model.occ.getCenterOfMass(2,t)[2]+16)<1e-7]
  g=gmsh.model.addPhysicalGroup(2,bottom);gmsh.model.setPhysicalName(2,g,'pad_bottom')
  g=gmsh.model.addPhysicalGroup(3,[t for d,t in vols]);gmsh.model.setPhysicalName(3,g,'seat')
  gmsh.model.occ.remove([(2,t) for d,t in gmsh.model.getEntities(2) if t not in boundary],recursive=False);gmsh.model.occ.synchronize()
  gmsh.option.setNumber('Mesh.MeshSizeMin',size);gmsh.option.setNumber('Mesh.MeshSizeMax',size);gmsh.option.setNumber('Mesh.MinimumCirclePoints',32);gmsh.option.setNumber('Mesh.MshFileVersion',2.2)
  gmsh.model.mesh.generate(3);path=a.out/f'seat_{size}.msh';gmsh.write(str(path))
 finally:gmsh.finalize()
 mesh=from_meshio(meshio.read(path));facets=mesh.boundaries['nut_bearing']
 if not set(facets).issubset(set(mesh.boundary_facets())):raise ValueError('internal load facets')
 x=mesh.p[:,mesh.facets[:,facets]];mesharea=np.linalg.norm(np.cross((x[:,1]-x[:,0]).T,(x[:,2]-x[:,0]).T),axis=1).sum()/2
 rows.append({'mesh_mm':size,'cad_area_mm2':area,'mesh_area_mm2':float(mesharea),'relative_area_error':float(abs(mesharea-area)/area),'volume_before_mm3':before,'volume_after_mm3':after,'passed':bool(abs(mesharea-area)/area<=.01)})
(a.out/'report.json').write_text(json.dumps({'rows':rows,'all_patch_checks_pass':all(r['passed'] for r in rows),'joint_verified':False},indent=2)+'\n');print(json.dumps(rows,indent=2))
