"""Imprint nominal nut and spacer bearing footprints on the cropped sole lock boss."""
import argparse,json,hashlib,math
from pathlib import Path
import gmsh,meshio,numpy as np
from skfem.io import from_meshio
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--seat-radius-mm',type=float,default=2);p.add_argument('--mesh-mm',type=float,nargs='+',default=[1,.7,.5]);a=p.parse_args();root=Path(__file__).resolve().parents[3];a.out.mkdir(parents=True,exist_ok=False);src=root/'validation/sole_lock_boss_screen_v1/boss.step';expected={'nut_bearing':16-math.pi*1.15**2,'spacer_bearing':math.pi*(a.seat_radius_mm**2-1.15**2)}
plan={'scope':__doc__,'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'seat_radius_mm':a.seat_radius_mm,'mesh_mm':a.mesh_mm,'expected_area_mm2':expected,'criteria':{'volume_error_mm3':1e-6,'cad_area_error_mm2':1e-6,'mesh_area_relative_error':.01},'limitations':['Nominal footprints only; edge chamfers, contact opening and friction not modeled.']};(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');rows=[]
for h in plan['mesh_mm']:
 gmsh.initialize()
 try:
  gmsh.option.setNumber('General.Terminal',0);vs=[v for v in gmsh.model.occ.importShapes(str(src)) if v[0]==3];before=sum(gmsh.model.occ.getMass(*v) for v in vs);nut=gmsh.model.occ.addRectangle(33,4,-14.2,4,4);seat=gmsh.model.occ.addDisk(35,6,-19,a.seat_radius_mm,a.seat_radius_mm);_,mapping=gmsh.model.occ.fragment(vs,[(2,nut),(2,seat)]);gmsh.model.occ.synchronize();vols=gmsh.model.getEntities(3);boundary={t for d,t in gmsh.model.getBoundary(vols,oriented=False) if d==2};after=sum(gmsh.model.occ.getMass(*v) for v in vols);assert len(vols)==1 and abs(after-before)<1e-6
  for name,items in zip(expected,mapping[-2:]):
   faces=[t for d,t in items if d==2 and t in boundary];area=sum(gmsh.model.occ.getMass(2,t) for t in faces);assert abs(area-expected[name])<1e-6;g=gmsh.model.addPhysicalGroup(2,faces);gmsh.model.setPhysicalName(2,g,name)
  g=gmsh.model.addPhysicalGroup(3,[v[1] for v in vols]);gmsh.model.setPhysicalName(3,g,'boss');gmsh.model.occ.remove([(2,t) for d,t in gmsh.model.getEntities(2) if t not in boundary],recursive=False);gmsh.model.occ.synchronize()
  for name,value in [('Mesh.MeshSizeMin',h),('Mesh.MeshSizeMax',h),('Mesh.MinimumCirclePoints',32),('Mesh.MshFileVersion',2.2)]:gmsh.option.setNumber(name,value)
  gmsh.model.mesh.generate(3);path=a.out/f'boss_{h:g}.msh';gmsh.write(str(path))
 finally:gmsh.finalize()
 mesh=from_meshio(meshio.read(path))
 for name,area in expected.items():
  ids=mesh.boundaries[name];assert set(ids)<=set(mesh.boundary_facets());x=mesh.p[:,mesh.facets[:,ids]];ma=np.linalg.norm(np.cross((x[:,1]-x[:,0]).T,(x[:,2]-x[:,0]).T),axis=1).sum()/2;rows.append({'mesh_mm':h,'patch':name,'mesh_area_mm2':float(ma),'relative_error':float(abs(ma-area)/area),'passed':bool(abs(ma-area)/area<=.01)})
r={'rows':rows,'passed':all(r['passed'] for r in rows),'joint_verified':False};(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
