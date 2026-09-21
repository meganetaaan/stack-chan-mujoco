"""Mesh both cropped parts together, then separate nodes while retaining identical contact triangles."""
import argparse,json,hashlib,math
from pathlib import Path
import gmsh,meshio,numpy as np
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--optimize-tets',action='store_true');p.add_argument('--fixed-anchor-points',action='store_true');p.add_argument('--out',type=Path,required=True);p.add_argument('--mesh-mm',type=float,default=.5);a=p.parse_args();root=Path(__file__).resolve().parents[3]
if a.out.exists() or not np.isfinite(a.mesh_mm) or a.mesh_mm<=0:p.error('new output and positive finite size required')
a.out.mkdir(parents=True)
paths={'BOSS':root/'validation/sole_lock_boss_screen_v1/boss.step','SPACER':root/'validation/sole_spacer_contact_geometry_v1/spacer.step'}
plan={'scope':__doc__,'optimize_tets':a.optimize_tets,'fixed_anchor_points':a.fixed_anchor_points,'mesh_mm':a.mesh_mm,'source_sha256':{str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in paths.values()},'criteria':{'volume_error_mm3':1e-6,'matching_contact_triangle_coordinates':True,'patch_area_relative_error':.01},'limitations':['Mesh preparation only; equal interface coordinates are duplicated in exported parts, not bonded.','Local cropped geometry and nominal bearing shapes remain assumptions.']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');gmsh.initialize()
try:
 gmsh.option.setNumber('General.Terminal',0);original=[];volumes_before=[]
 for path in paths.values():
  v=[x for x in gmsh.model.occ.importShapes(str(path)) if x[0]==3];assert len(v)==1;original+=v;volumes_before.append(gmsh.model.occ.getMass(*v[0]))
 nut=gmsh.model.occ.addRectangle(33,4,-14.2,4,4);head=gmsh.model.occ.addDisk(35,6,-19.85,1.9,1.9)
 anchor_tools=[]
 if a.fixed_anchor_points:
  for q in [[32.1,6,-19.85],[37.9,6,-19.85],[35,8.9,-19.85]]:anchor_tools.append((0,gmsh.model.occ.addPoint(*q)))
 _,mapping=gmsh.model.occ.fragment(original,[(2,nut),(2,head)]+anchor_tools);gmsh.model.occ.synchronize()
 vols=[]
 for items,before in zip(mapping[:2],volumes_before):
  v=[x for x in items if x[0]==3];assert len(v)==1 and abs(gmsh.model.occ.getMass(*v[0])-before)<1e-6;vols.append(v[0])
 boundaries=[{t for d,t in gmsh.model.getBoundary([v],oriented=False) if d==2} for v in vols];contact=boundaries[0]&boundaries[1];assert contact
 area=sum(gmsh.model.occ.getMass(2,t) for t in contact);assert abs(area-math.pi*(2.925**2-1.225**2))<1e-6
 patchsets={'contact':contact,'nut_bearing':{t for d,t in mapping[2] if d==2 and t in boundaries[0]},'head_bearing':{t for d,t in mapping[3] if d==2 and t in boundaries[1]}}
 expected={'contact':math.pi*(2.925**2-1.225**2),'nut_bearing':16-math.pi*1.15**2,'head_bearing':math.pi*(1.9**2-1.225**2)}
 for name,ss in patchsets.items():
  assert abs(sum(gmsh.model.occ.getMass(2,t) for t in ss)-expected[name])<1e-6
  g=gmsh.model.addPhysicalGroup(2,list(ss));gmsh.model.setPhysicalName(2,g,name)
 for name,v in zip(paths,vols):
  g=gmsh.model.addPhysicalGroup(3,[v[1]]);gmsh.model.setPhysicalName(3,g,name)
 used=set.union(*boundaries);gmsh.model.occ.remove([(2,t) for d,t in gmsh.model.getEntities(2) if t not in used],recursive=False);gmsh.model.occ.synchronize()
 gmsh.option.setNumber('Mesh.MeshSizeMin',a.mesh_mm);gmsh.option.setNumber('Mesh.MeshSizeMax',a.mesh_mm);gmsh.option.setNumber('Mesh.MinimumCirclePoints',32);gmsh.option.setNumber('Mesh.MshFileVersion',2.2);gmsh.model.mesh.generate(3)
 if a.optimize_tets:gmsh.model.mesh.optimize('Netgen')
 gmsh.write(str(a.out/'combined.msh'))
finally:gmsh.finalize()
m=meshio.read(a.out/'combined.msh');reports=[];contact_keys=[]
for name,contactname,loadname,filename in [('BOSS','spacer_contact','nut_bearing','boss'),('SPACER','boss_contact','head_bearing','spacer')]:
 tet=m.cells_dict['tetra'][m.cell_data_dict['gmsh:physical']['tetra']==m.field_data[name][0]];tris=[];tags=[];fields={name:np.array([3,3])}
 for tag,(old,new) in enumerate([('contact',contactname),(loadname,loadname)],1):
  t=m.cells_dict['triangle'][m.cell_data_dict['gmsh:physical']['triangle']==m.field_data[old][0]];tris.extend(t);tags.extend([tag]*len(t));fields[new]=np.array([tag,2]);x=m.points[t];ma=np.linalg.norm(np.cross(x[:,1]-x[:,0],x[:,2]-x[:,0]),axis=1).sum()/2
  reports.append({'part':name,'patch':new,'mesh_area_mm2':float(ma),'expected_mm2':expected[old],'relative_error':float(abs(ma-expected[old])/expected[old])})
  if old=='contact':contact_keys.append(sorted(tuple(sorted(tuple(np.round(q,10)) for q in tri)) for tri in x))
 tris=np.array(tris);used=np.unique(tet);assert set(tris.flatten())<=set(used);remap=np.full(len(m.points),-1);remap[used]=np.arange(len(used))
 outmesh=meshio.Mesh(m.points[used],[('triangle',remap[tris]),('tetra',remap[tet])],cell_data={'gmsh:physical':[np.array(tags),np.full(len(tet),3)],'gmsh:geometrical':[np.array(tags),np.full(len(tet),3)]},field_data=fields)
 folder=a.out/name.lower();folder.mkdir();meshio.write(folder/f'{filename}_{a.mesh_mm:g}.msh',outmesh,file_format='gmsh22',binary=False)
matched=contact_keys[0]==contact_keys[1];r={'patches':reports,'matching_contact_triangles':matched,'contact_triangles_per_part':len(contact_keys[0]),'passed':matched and all(x['relative_error']<.01 for x in reports),'joint_verified':False};(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
