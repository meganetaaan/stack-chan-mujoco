"""Balanced local boot/yoke contact with both actual cropped parts deformable."""
import argparse,collections,hashlib,json,os,subprocess
from pathlib import Path
import meshio,numpy as np
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--boot-mesh-dir',type=Path);p.add_argument('--yoke-mesh-dir',type=Path);p.add_argument('--reverse-contact',action='store_true');p.add_argument('--out',type=Path,required=True);p.add_argument('--mesh-mm',default='0.7');a=p.parse_args()
root=Path(__file__).resolve().parents[3]
if a.out.exists():p.error('new output required')
a.out.mkdir(parents=True)
paths={'BOOT':(a.boot_mesh_dir or root/'validation/boot_nut_patch_development_v1')/f'seat_{a.mesh_mm}.msh','YOKE':(a.yoke_mesh_dir or root/'validation/local_yoke_contact_mesh_v1')/f'yoke_{a.mesh_mm}.msh'}
plan={'scope':__doc__,'reverse_contact':a.reverse_contact,'mesh_mm':float(a.mesh_mm),'force_each_N':20,'penalty_N_mm3':1e6,'E_MPa':1120,'poisson':.35,'source_sha256':{str(f.resolve().relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in paths.values()},'criteria':{'solver_completion':True,'relative_anchor_force':1e-4,'maximum_penetration_mm':.01},'limitations':['Cropped geometry with free cut faces, not full yoke/boot.','Balanced nominal forces substitute screw/nut elasticity and actual preload.','Single C3D4 mesh; no creep or walking loads.']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
lines=['*HEADING',__doc__];offset=0;eo=0;anchors=[];constraints=[];loads={};total_force=np.zeros(3);total_moment=np.zeros(3);node_xyz={}
face_indices=[(0,1,2),(0,3,1),(1,3,2),(2,3,0)]
for name,path in paths.items():
 m=meshio.read(path);xyz=m.points;tet=m.cells_dict['tetra'];tri=m.cells_dict['triangle'];tags=m.cell_data_dict['gmsh:physical']['triangle']
 volumes=np.einsum('ij,ij->i',np.cross(xyz[tet[:,1]]-xyz[tet[:,0]],xyz[tet[:,2]]-xyz[tet[:,0]]),xyz[tet[:,3]]-xyz[tet[:,0]])/6
 if not np.all(volumes>0):raise ValueError('nonpositive tet')
 lines += [f'*NODE,NSET={name}']+[f'{offset+i+1},'+','.join(map(str,q)) for i,q in enumerate(xyz)]
 node_xyz.update({offset+i+1:q for i,q in enumerate(xyz)})
 lines += [f'*ELEMENT,TYPE=C3D4,ELSET={name}']+[f'{eo+i+1},'+','.join(str(offset+int(n)+1) for n in nodes) for i,nodes in enumerate(tet)]
 lookup=collections.defaultdict(list)
 for i,nodes in enumerate(tet):
  for j,ind in enumerate(face_indices):lookup[tuple(sorted(nodes[list(ind)]))].append((eo+i+1,j+1))
 contact='pad_bottom' if name=='BOOT' else 'boot_contact';loaded='nut_bearing' if name=='BOOT' else 'head_bearing'
 ts=tri[tags==m.field_data[contact][0]];lines += [f'*SURFACE,NAME={name}_CONTACT,TYPE=ELEMENT']
 for t in ts:
  hit=lookup[tuple(sorted(t))]
  if len(hit)!=1:raise ValueError('non-exterior contact face')
  e,f=hit[0];lines.append(f'{e},S{f}')
 ts=tri[tags==m.field_data[loaded][0]];areas=np.linalg.norm(np.cross(xyz[ts[:,1]]-xyz[ts[:,0]],xyz[ts[:,2]]-xyz[ts[:,0]]),axis=1)/2
 force=-20 if name=='BOOT' else 20
 for t,area in zip(ts,areas):
  for n in t:
   key=offset+int(n)+1;loads[key]=loads.get(key,0)+force*area/areas.sum()/3
 # Geometrically separated anchors; yoke has 3-2-1 constraints, boot only in-plane.
 targets=[[-38,-18.5,-19],[-30,-18.5,-19],[-38,-10.5,-19]] if name=='YOKE' else [[-38,-18.5,-16],[-30,-18.5,-16]]
 ids=[int(np.argmin(np.linalg.norm(xyz-q,axis=1)))+offset+1 for q in np.array(targets)]
 if len(set(ids))!=len(ids):raise ValueError('duplicate anchors')
 if name=='YOKE':constraints += [f'{ids[0]},1,3,0',f'{ids[1]},2,3,0',f'{ids[2]},3,3,0']
 else:constraints += [f'{ids[0]},1,2,0',f'{ids[1]},2,2,0']
 anchors.extend(ids);offset+=len(xyz);eo+=len(tet)
for n,f in loads.items():total_force += [0,0,f];total_moment += np.cross(node_xyz[n],[0,0,f])
if np.linalg.norm(total_force)>1e-8 or np.linalg.norm(total_moment)>1e-7:raise ValueError('unbalanced input load')
for name in paths:lines += [f'*MATERIAL,NAME={name}','*ELASTIC','1120,.35',f'*SOLID SECTION,ELSET={name},MATERIAL={name}']
lines+=['*NSET,NSET=ANCHORS',','.join(map(str,anchors)),'*SURFACE INTERACTION,NAME=NORMAL','*SURFACE BEHAVIOR,PRESSURE-OVERCLOSURE=LINEAR','1000000','*CONTACT PAIR,INTERACTION=NORMAL,TYPE=SURFACE TO SURFACE',('YOKE_CONTACT,BOOT_CONTACT' if a.reverse_contact else 'BOOT_CONTACT,YOKE_CONTACT'),'*BOUNDARY',*constraints,'*STEP,NLGEOM,INC=100','*STATIC','.1,1,1e-6,.1','*CLOAD']+[f'{n},3,{f:.15g}' for n,f in sorted(loads.items())]
lines+=['*NODE PRINT,NSET=ANCHORS,TOTALS=ONLY','RF','*NODE PRINT,NSET=BOOT','U','*NODE PRINT,NSET=YOKE','U',('*CONTACT PRINT,SLAVE=YOKE_CONTACT,MASTER=BOOT_CONTACT' if a.reverse_contact else '*CONTACT PRINT,SLAVE=BOOT_CONTACT,MASTER=YOKE_CONTACT'),'CF,CDIS,CSTR','*END STEP']
(a.out/'contact.inp').write_text('\n'.join(lines)+'\n');(a.out/'assembly.json').write_text(json.dumps({'force_N':total_force.tolist(),'moment_Nmm':total_moment.tolist(),'anchors':{str(n):node_xyz[n].tolist() for n in anchors}},indent=2)+'\n')
exe=root/'.tools/root/usr/bin/ccx';env=os.environ.copy();env['LD_LIBRARY_PATH']=str(root/'.tools/root/usr/lib/x86_64-linux-gnu');env['OMP_NUM_THREADS']='1'
r=subprocess.run([str(exe),'-i','contact'],cwd=a.out.resolve(),env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
(a.out/'solver.log').write_text(r.stdout);ok=r.returncode==0 and 'Job finished' in r.stdout and '*ERROR' not in r.stdout
(a.out/'run.json').write_text(json.dumps({'returncode':r.returncode,'solver_completed':ok,'executable_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'physical_gates_evaluated':False},indent=2)+'\n');print(json.dumps({'solver_completed':ok}));raise SystemExit(0 if ok else 1)
