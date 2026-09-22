"""Balanced washer-pressure contact probe on current body and plate, not screw qualification."""
import argparse,hashlib,json,os,subprocess
from pathlib import Path
import numpy as np
import meshio
ROOT=Path(__file__).resolve().parents[3]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--out',type=Path,required=True)
p.add_argument('--force-per-corner',type=float,default=25.)
p.add_argument('--penalty',type=float,default=1e5)
a=p.parse_args();assert a.force_per_corner>0 and a.penalty>0
a.out.mkdir(parents=True,exist_ok=False)
source=ROOT/'validation/rear_contact_assembly_mesh_development_v1'
blocks=[]
for line in (source/'ccx_v1/mesh_surfaces.inp').read_text().splitlines():
 if line.startswith('*'):blocks.append([line])
 else:blocks[-1].append(line)
chosen=[]; surfaces={}
for block in blocks:
 head=block[0]
 keep=any(head.endswith('='+part) or ('NAME='+part+'__') in head for part in ['body','rear_plate'])
 if keep:
  chosen+=block
  if head.startswith('*SURFACE'):surfaces[head.split('NAME=')[1].split(',')[0]]=block[1:]
constraints=[];offset=0;anchors={};pressure_rows=[];dloads=[]
for part in ['body','rear_plate']:
 m=meshio.read(source/'mesh_v1'/(part+'.msh'))
 xyz=m.points
 targets=[[-62.2,-64,0],[-62.2,64,0],[-62.2,-64,128]] if part=='body' else [[-64.2,-64,0],[-64.2,64,0]]
 dofs=[(1,3),(1,1),(3,3),(1,1)] if part=='body' else [(2,3),(3,3)]
 ns=[int(np.argmin(np.linalg.norm(xyz-np.array(t),axis=1))) for t in targets]
 assert len(set(ns))==len(ns)
 anchors[part]=[{'node':n+offset+1,'xyz':xyz[n].tolist()} for n in ns]
 if part=='body':
  constraints += [f'{ns[0]+offset+1},1,3,0',f'{ns[1]+offset+1},1,1,0',f'{ns[1]+offset+1},3,3,0',f'{ns[2]+offset+1},1,1,0']
 else:constraints += [f'{ns[0]+offset+1},2,3,0',f'{ns[1]+offset+1},3,3,0']
 checks=json.loads((source/'mesh_v1'/(part+'.json')).read_text())['contacts']
 for c in checks:
  if 'washer' not in c['name']:continue
  pressure=a.force_per_corner/c['mesh_area_mm2']
  pressure_rows.append({'part':part,'contact':c['name'],'pressure_MPa':pressure,'force_N':a.force_per_corner})
  for row in surfaces[part+'__'+c['name']]:
   eid,face=row.split(',');dloads.append(f'{eid},P{face[1:]},{pressure:.15g}')
 offset+=len(xyz)
plan={'scope':__doc__,'force_per_corner_N':a.force_per_corner,'penalty_N_mm3':a.penalty,
 'materials':{'body':{'E_MPa':1120,'nu':.35},'rear_plate':{'E_MPa':68300,'nu':.33}},
 'anchors':anchors,'pressure_loads':pressure_rows,
 'criteria':{'solver_completion':True,'relative_total_anchor_force_max':1e-4},
 'limitations':['normal pressure replaces screw and washer compliance','frictionless contact',
 'minimal rigid-mode anchors; anchor reaction must be evaluated','C3D4 mesh not stiffness-converged',
 'no walking load, thread strength, retained preload, friction or tolerance qualification'],
 'mesh_sha256':hashlib.sha256((source/'ccx_v1/mesh_surfaces.inp').read_bytes()).hexdigest()}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
lines=['*HEADING',__doc__,*chosen]
for part,material in plan['materials'].items():
 lines += [f'*MATERIAL,NAME={part}','*ELASTIC',f"{material['E_MPa']},{material['nu']}",f'*SOLID SECTION,ELSET={part},MATERIAL={part}']
anchor_nodes=sorted({x['node'] for rows in anchors.values() for x in rows})
lines += ['*NSET,NSET=ANCHORS',','.join(map(str,anchor_nodes)),
 '*SURFACE INTERACTION,NAME=NORMAL','*SURFACE BEHAVIOR,PRESSURE-OVERCLOSURE=LINEAR',str(a.penalty),
 '*CONTACT PAIR,INTERACTION=NORMAL,TYPE=SURFACE TO SURFACE','rear_plate__body_plate,body__body_plate',
 '*BOUNDARY',*constraints,'*STEP,NLGEOM,INC=200','*STATIC','.05,1,1e-6,.1','*DLOAD',*dloads,
 '*NODE PRINT,NSET=ANCHORS','RF','*NODE PRINT,NSET=ANCHORS,TOTALS=ONLY','RF',
 '*NODE FILE','U','*EL FILE','S','*CONTACT PRINT,SLAVE=rear_plate__body_plate,MASTER=body__body_plate','CF,CDIS,CSTR','*END STEP']
(a.out/'contact.inp').write_text('\n'.join(lines)+'\n')
exe=ROOT/'.tools/root/usr/bin/ccx';env=os.environ.copy();env['OMP_NUM_THREADS']='1'
env['LD_LIBRARY_PATH']=str(ROOT/'.tools/root/usr/lib/x86_64-linux-gnu')
with (a.out/'solver.log').open('w') as log:
 result=subprocess.run([str(exe),'-i','contact'],cwd=a.out.resolve(),env=env,stdout=log,stderr=subprocess.STDOUT)
log=(a.out/'solver.log').read_text()
(a.out/'run.json').write_text(json.dumps({'returncode':result.returncode,'solver_finished':result.returncode==0 and 'Job finished' in log and '*ERROR' not in log,
 'executable_sha256':hashlib.sha256(exe.read_bytes()).hexdigest()},indent=2)+'\n')
print((a.out/'run.json').read_text())
