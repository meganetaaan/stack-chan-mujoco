"""Mesh actual cropped yoke with screw-head and boot-seat bearing patches."""
import argparse,hashlib,json,math
from pathlib import Path
import cadquery as cq
import gmsh,meshio,numpy as np
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[3]
if a.out.exists():p.error('new output required')
a.out.mkdir(parents=True)
source=root/'validation/native_horn_yoke_development_v1/v4/left_foot_yoke.step'
plan={'scope':__doc__,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'crop_xy_mm':[[-38,-30],[-18.5,-10.5]],'crop_z_mm':[-19,-16],'patches':{'boot_contact':{'z':-16,'radius':3},'head_bearing':{'z':-19,'radius':1.9}},'hole_radius_mm':1.15,'mesh_mm':[1,.7,.5],'criteria':{'cad_area_error_mm2':1e-6,'mesh_area_relative_error':.01,'volume_change_mm3':1e-6},'limitations':['Cut side faces omit surrounding yoke stiffness.','Nominal patches, no screw-head fillet or tolerance.','Mesh preparation only; not a contact solve.']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
shape=cq.importers.importStep(str(source)).val().intersect(cq.Workplane('XY').box(8,8,3).val().translate((-34,-14.5,-17.5)))
if not shape.isValid() or len(shape.Solids())!=1:raise ValueError('invalid crop')
step=a.out/'local_yoke.step';cq.exporters.export(shape,str(step));rows=[]
for size in plan['mesh_mm']:
 gmsh.initialize()
 try:
  gmsh.option.setNumber('General.Terminal',0);vols=[v for v in gmsh.model.occ.importShapes(str(step)) if v[0]==3];before=sum(gmsh.model.occ.getMass(*v) for v in vols)
  patches=[(name,gmsh.model.occ.addDisk(-34,-14.5,d['z'],d['radius'],d['radius']),math.pi*(d['radius']**2-1.15**2)) for name,d in plan['patches'].items()]
  _,mapping=gmsh.model.occ.fragment(vols,[(2,t) for n,t,e in patches]);gmsh.model.occ.synchronize();vols=gmsh.model.getEntities(3)
  boundary={t for d,t in gmsh.model.getBoundary(vols,oriented=False) if d==2};after=sum(gmsh.model.occ.getMass(*v) for v in vols);areas={}
  if len(vols)!=1 or abs(after-before)>1e-6:raise ValueError('volume changed')
  for (name,tag,expected),mapped in zip(patches,mapping[1:]):
   faces=[t for d,t in mapped if d==2 and t in boundary];area=sum(gmsh.model.occ.getMass(2,t) for t in faces)
   if abs(area-expected)>1e-6:raise ValueError(f'patch mismatch {name}: {area} vs {expected}')
   g=gmsh.model.addPhysicalGroup(2,faces);gmsh.model.setPhysicalName(2,g,name);areas[name]=area
  g=gmsh.model.addPhysicalGroup(3,[t for d,t in vols]);gmsh.model.setPhysicalName(3,g,'yoke')
  gmsh.model.occ.remove([(2,t) for d,t in gmsh.model.getEntities(2) if t not in boundary],recursive=False);gmsh.model.occ.synchronize()
  gmsh.option.setNumber('Mesh.MeshSizeMin',size);gmsh.option.setNumber('Mesh.MeshSizeMax',size);gmsh.option.setNumber('Mesh.MinimumCirclePoints',32);gmsh.option.setNumber('Mesh.MshFileVersion',2.2);gmsh.model.mesh.generate(3);path=a.out/f'yoke_{size}.msh';gmsh.write(str(path))
 finally:gmsh.finalize()
 m=meshio.read(path);checks={}
 for name,area in areas.items():
  tris=m.cells_dict['triangle'][m.cell_data_dict['gmsh:physical']['triangle']==m.field_data[name][0]];x=m.points[tris];ma=np.linalg.norm(np.cross(x[:,1]-x[:,0],x[:,2]-x[:,0]),axis=1).sum()/2
  checks[name]={'cad_area_mm2':area,'mesh_area_mm2':float(ma),'relative_error':float(abs(ma-area)/area),'passed':bool(abs(ma-area)/area<.01)}
 rows.append({'mesh_mm':size,'volume_mm3':after,'patches':checks})
(a.out/'report.json').write_text(json.dumps({'rows':rows,'all_patch_checks_pass':all(c['passed'] for r in rows for c in r['patches'].values()),'joint_verified':False},indent=2)+'\n');print(json.dumps(rows,indent=2))
