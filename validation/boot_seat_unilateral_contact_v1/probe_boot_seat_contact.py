"""Unilateral local boot-seat contact probe against an ideal fixed support block."""
import argparse,collections,hashlib,json,os,subprocess
from pathlib import Path
import meshio,numpy as np
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[3]
if a.out.exists():p.error('new output required')
a.out.mkdir(parents=True)
source=root/'validation/boot_nut_patch_development_v1/seat_0.7.msh';m=meshio.read(source);xyz=m.points;tet=m.cells_dict['tetra'];tri=m.cells_dict['triangle'];tags=m.cell_data_dict['gmsh:physical']['triangle']
indices=[(0,1,2),(0,3,1),(1,3,2),(2,3,0)];lookup=collections.defaultdict(list)
v=np.einsum('ij,ij->i',np.cross(xyz[tet[:,1]]-xyz[tet[:,0]],xyz[tet[:,2]]-xyz[tet[:,0]]),xyz[tet[:,3]]-xyz[tet[:,0]])/6
if not np.all(v>0):raise ValueError('nonpositive tetrahedron')
for i,nodes in enumerate(tet):
 for j,ind in enumerate(indices):lookup[tuple(sorted(nodes[list(ind)]))].append((i+1,j+1))
surfaces={};loads=collections.defaultdict(float)
for name in ('pad_bottom','nut_bearing'):
 ts=tri[tags==m.field_data[name][0]];mapped=[]
 for t in ts:
  matches=lookup[tuple(sorted(t))]
  if len(matches)!=1:raise ValueError('not exterior face')
  mapped.append(matches[0])
 surfaces[name]=mapped
 if name=='nut_bearing':
  areas=np.linalg.norm(np.cross(xyz[ts[:,1]]-xyz[ts[:,0]],xyz[ts[:,2]]-xyz[ts[:,0]]),axis=1)/2
  for t,area in zip(ts,areas):
   for n in t:loads[int(n)+1]+=-20*area/areas.sum()/3
bottom_nodes=np.unique(tri[tags==m.field_data['pad_bottom'][0]])
na=int(bottom_nodes[np.argmin(xyz[bottom_nodes,0])])+1;nb=int(bottom_nodes[np.argmax(xyz[bottom_nodes,0])])+1
plan={'scope':__doc__,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'force_N':20,'penalty_N_mm3':1e5,'material':{'E_MPa':1120,'poisson':.35},'anchors':{'xy_node':na,'y_node':nb},'criteria':{'solver_completion':True,'relative_force_balance':1e-4,'penetration_mm':.01},'limitations':['C3D4 single mesh; not comparable directly to quadratic FE peaks.','Ideal fixed support block; no deformable yoke or actual nut contact.','No walking loads, creep, thread or fastener preload qualification.']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
lines=['*HEADING',__doc__,'*NODE,NSET=SEAT']+[f'{i+1},'+','.join(map(str,pt)) for i,pt in enumerate(xyz)]
lines+=['*ELEMENT,TYPE=C3D4,ELSET=SEAT']+[f'{i+1},'+','.join(str(int(n)+1) for n in ns) for i,ns in enumerate(tet)]
base=len(xyz);block=[(-39,-19.5,-17),(-29,-19.5,-17),(-29,-9.5,-17),(-39,-9.5,-17),(-39,-19.5,-16),(-29,-19.5,-16),(-29,-9.5,-16),(-39,-9.5,-16)]
lines+=['*NODE,NSET=SUPPORT']+[f'{base+i+1},'+','.join(map(str,pt)) for i,pt in enumerate(block)]
lines+=['*ELEMENT,TYPE=C3D8,ELSET=SUPPORT',f'{len(tet)+1},'+','.join(str(base+i+1) for i in range(8))]
for name in ('SEAT','SUPPORT'):lines += [f'*MATERIAL,NAME={name}','*ELASTIC','1120,.35',f'*SOLID SECTION,ELSET={name},MATERIAL={name}']
lines+=['*SURFACE,NAME=SLAVE,TYPE=ELEMENT']+[f'{e},S{f}' for e,f in surfaces['pad_bottom']]
lines+=['*SURFACE,NAME=MASTER,TYPE=ELEMENT','SUPPORT,S2','*SURFACE INTERACTION,NAME=NORMAL','*SURFACE BEHAVIOR,PRESSURE-OVERCLOSURE=LINEAR','100000','*CONTACT PAIR,INTERACTION=NORMAL,TYPE=SURFACE TO SURFACE','SLAVE,MASTER','*NSET,NSET=ANCHORS',f'{na},{nb}','*BOUNDARY','SUPPORT,1,3,0',f'{na},1,2,0',f'{nb},2,2,0','*STEP,NLGEOM,INC=100','*STATIC','.1,1,1e-6,.1','*CLOAD']+[f'{n},3,{f:.15g}' for n,f in loads.items()]
lines+=['*NODE PRINT,NSET=SUPPORT,TOTALS=ONLY','RF','*NODE PRINT,NSET=ANCHORS,TOTALS=ONLY','RF','*NODE PRINT,NSET=SEAT','U','*CONTACT PRINT,SLAVE=SLAVE,MASTER=MASTER','CF,CDIS,CSTR','*END STEP']
(a.out/'contact.inp').write_text('\n'.join(lines)+'\n')
env=os.environ.copy();env['LD_LIBRARY_PATH']=str(root/'.tools/root/usr/lib/x86_64-linux-gnu');env['OMP_NUM_THREADS']='1';exe=root/'.tools/root/usr/bin/ccx'
r=subprocess.run([str(exe),'-i','contact'],cwd=a.out.resolve(),env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
(a.out/'solver.log').write_text(r.stdout)
passed=r.returncode==0 and 'Job finished' in r.stdout and '*ERROR' not in r.stdout
(a.out/'run.json').write_text(json.dumps({'returncode':r.returncode,'solver_completed':passed,'executable_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'physical_gates_evaluated':False},indent=2)+'\n')
print(json.dumps({'solver_completed':passed,'returncode':r.returncode}));raise SystemExit(0 if passed else 1)
