"""Export independent tetrahedra and verified contact faces; not a runnable solve."""
import argparse, collections, hashlib, json
from pathlib import Path
import meshio
import numpy as np
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--mesh-dir',type=Path,required=True)
p.add_argument('--out',type=Path,required=True)
a=p.parse_args(); a.out.mkdir(parents=True,exist_ok=False)
plan=json.loads((a.mesh_dir/'plan.json').read_text())
assert len(plan['parts'])==18, 'All hardware required'
criteria={'all_contact_triangles_are_unique_exterior_tet_faces':True,'positive_tetrahedron_volume':True,
          'each_contact_has_two_sides':True,'opposite_mean_normal_dot_max':-.999999}
(a.out/'plan.json').write_text(json.dumps({'scope':__doc__,'criteria':criteria,
 'face_number_source':'CalculiX 2.21 manual section 7.43, tetrahedral faces',
 'input_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(a.mesh_dir.glob('*.msh'))},
 'limitations':['no material, boundary, connector, preload or load specification',
 'linear tetrahedral stiffness requires convergence assessment','thread envelope overlap remains unresolved']},indent=2)+'\n')
face_indices=[(0,1,2),(0,3,1),(1,3,2),(2,3,0)]
lines=['** Mesh and contact surface definitions only; NOT a runnable or qualified joint model']
node_offset=0; elem_offset=0; pairs=collections.defaultdict(list); rows=[]
for part in plan['parts']:
 m=meshio.read(a.mesh_dir/(part+'.msh'))
 tet=m.cells_dict['tetra'].copy(); xyz=m.points
 v=np.einsum('ij,ij->i',np.cross(xyz[tet[:,1]]-xyz[tet[:,0]],xyz[tet[:,2]]-xyz[tet[:,0]]),xyz[tet[:,3]]-xyz[tet[:,0]])/6
 assert np.all(v>0),part
 faces=collections.defaultdict(list)
 for ei,nodes in enumerate(tet):
  for fi,ind in enumerate(face_indices):faces[tuple(sorted(nodes[list(ind)]))].append((ei+elem_offset+1,fi+1))
 lines += [f'*NODE,NSET={part}']
 lines += [f'{i+node_offset+1},'+','.join(f'{x:.12g}' for x in point) for i,point in enumerate(xyz)]
 lines += [f'*ELEMENT,TYPE=C3D4,ELSET={part}']
 lines += [f'{i+elem_offset+1},'+','.join(str(int(n)+node_offset+1) for n in ns) for i,ns in enumerate(tet)]
 tris=m.cells_dict['triangle']; tags=m.cell_data_dict['gmsh:physical']['triangle']
 for name,(tag,dim) in m.field_data.items():
  if dim!=2:continue
  selected=tris[tags==tag]; assert len(selected)
  mapped=[]; normals=[]
  for tri in selected:
   matches=faces[tuple(sorted(tri))];assert len(matches)==1,(part,name,matches)
   eid,face=matches[0]; mapped.append((eid,face))
   nodes=tet[eid-elem_offset-1]; pts=xyz[nodes[list(face_indices[face-1])]]
   normal=np.cross(pts[1]-pts[0],pts[2]-pts[0])
   # Orient outward independently of the documented node ordering.
   if np.dot(normal,xyz[nodes].mean(axis=0)-pts.mean(axis=0))>0:normal=-normal
   normals.append(normal)
  assert len(mapped)==len(set(mapped))
  surface=f'{part}__{name}'
  lines += [f'*SURFACE,NAME={surface},TYPE=ELEMENT']+[f'{e},S{f}' for e,f in mapped]
  normal=np.sum(normals,axis=0);normal/=np.linalg.norm(normal)
  pairs[name].append({'part':part,'surface':surface,'triangles':len(mapped),'mean_outward_normal':normal.tolist()})
 rows.append({'part':part,'nodes':len(xyz),'elements':len(tet),'minimum_volume_mm3':float(v.min())})
 node_offset+=len(xyz);elem_offset+=len(tet)
checks=[]
for name,sides in pairs.items():
 assert len(sides)==2,(name,sides)
 dot=float(np.dot(sides[0]['mean_outward_normal'],sides[1]['mean_outward_normal']))
 assert dot<criteria['opposite_mean_normal_dot_max'],(name,dot)
 checks.append({'contact':name,'sides':sides,'normal_dot':dot})
assert len(checks)==17
(a.out/'mesh_surfaces.inp').write_text('\n'.join(lines)+'\n')
(a.out/'report.json').write_text(json.dumps({'parts':rows,'contacts':checks,'nodes':node_offset,'elements':elem_offset,
 'geometry_mapping_passed':True,'joint_strength_verified':False,'preload_verified':False},indent=2)+'\n')
print(json.dumps({'parts':len(rows),'contact_pairs':len(checks),'nodes':node_offset,'elements':elem_offset}))
