"""Package the current yaw-support candidate without claiming assembly qualification."""
import argparse,hashlib,json
from pathlib import Path
import cadquery as cq
ROOT=Path(__file__).resolve().parents[3];p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--moments',action='store_true');p.add_argument('--rear-washer-dir',type=Path);p.add_argument('--support-dir',type=Path);p.add_argument('--plate-dir',type=Path);p.add_argument('--plate-washer-dir',type=Path);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
assy=cq.Assembly(name='yaw_support_candidate');rows=[];moments=[]
if a.moments:
 import numpy as np
 from OCP.GProp import GProp_GProps
 from OCP.BRepGProp import BRepGProp
 def geometric_properties(shape):
  props=GProp_GProps();BRepGProp.VolumeProperties_s(shape.wrapped,props)
  center=props.CentreOfMass();matrix=props.MatrixOfInertia()
  return props.Mass(),[center.X(),center.Y(),center.Z()],[[matrix.Value(i,j) for j in range(1,4)] for i in range(1,4)]
 # Analytic translated box verifies units and central (not origin) inertia.
 box=cq.Solid.makeBox(2,3,4,cq.Vector(10,20,30))
 volume,center,matrix=geometric_properties(box)
 assert abs(volume-24)<1e-9 and max(abs(x-y) for x,y in zip(center,[11,21.5,32]))<1e-9
 assert max(abs(matrix[i][j]-([50,40,26][i] if i==j else 0)) for i in range(3) for j in range(3))<1e-8

def add(name,s,source=None,note='nominal geometry'):
 assert s.isValid()
 assy.add(s,name=name);r={'name':name,'solids':len(s.Solids()),'volume_mm3':s.Volume(),'source':source,'note':note}
 if source:r['source_sha256']=hashlib.sha256((ROOT/source).read_bytes()).hexdigest()
 rows.append(r)
 if a.moments:
  volume,center,matrix=geometric_properties(s)
  assert abs(volume-s.Volume())<1e-6
  eigenvalues=np.linalg.eigvalsh(matrix)
  assert eigenvalues[0]>0 and eigenvalues[-1]<=sum(eigenvalues[:2])+1e-6
  eligible=name in ('body_shroud','rear_plate') or name.endswith(('yaw_fixed_support','threaded_backing_plate','mount_plate','rear_washer')) or ('_plate_' in name and name.endswith('_washer'))
  moments.append({'name':name,'volume_mm3':volume,'com_assembly_m':[v*.001 for v in center],'mass_kg_per_density_kg_m3':volume*1e-9,'inertia_com_kg_m2_per_density_kg_m3':[[v*1e-15 for v in row] for row in matrix],'use_for_material_mass':eligible,'restriction':'homogeneous nominal solid only; process/material qualification pending' if eligible else 'collision/fastener envelope; not physical mass evidence'})

def read(name,path,shift=None,note='nominal geometry'):
 s=cq.importers.importStep(str(ROOT/path)).val()
 if shift:s=s.translate(shift)
 add(name,s,path,note)
read('body_shroud','validation/yaw_tool_access_v1/body_shroud.step')
read('rear_plate','validation/rear_joint_assembly_development_v1/rear_joint_inset2_v1/rear_structural_plate.step')
for side,cy in [('left',26),('right',-26)]:
 for name in ['yaw_fixed_support','threaded_backing_plate']:
  read(side+'_'+name,str(a.support_dir/f'{side}_{name}.step') if name=='yaw_fixed_support' and a.support_dir else f'validation/yaw_backing_keeper_v2/{side}_{name}.step')
 read(side+'_mount_plate',str(a.plate_dir/f'{side}_mount_plate.step') if a.plate_dir else f'validation/yaw_metal_seat_v4/{side}_mount_plate.step')
 for z in [64,76]:read(f'{side}_{z}_keeper',f'validation/yaw_backing_keeper_v2/{side}_{z}_keeper_envelope.step',note='NBK SLH-M2-10 nominal; thread overlap intentional')
 for i in range(4):
  for name in ['bolt','rear_washer']:
   if name=='rear_washer' and a.rear_washer_dir:
    read(f'{side}_rear_{i}_{name}',str(a.rear_washer_dir/f'{side}_rear_{i}_{name}.step'),note='SCW-YAW-REAR-WASHER-01 revA proposal; already in assembly coordinates')
   else:
    read(f'{side}_rear_{i}_{name}',f'validation/inset_yaw_assembly_development_v1/inset_fasteners_staged_v2/{side}_{i}_{name}.step',(-.2,0,0),'M3 hardware envelope moved to 2 mm rear plate; inner nut/washer replaced by threaded plate')
 for i,(x,y) in enumerate(( (x,y) for x in [-34,8.1] for y in [cy-10,cy+10])):
  def cyl(r,h,z):return cq.Solid.makeCylinder(r,h,cq.Vector(x,y,z))
  add(f'{side}_plate_{i}_screw',cyl(1.9,1.3,86.7).fuse(cyl(1,10,88)),note='NBK SLH-M2-10 nominal envelope')
  if a.plate_washer_dir:
   read(f'{side}_plate_{i}_washer',str(a.plate_washer_dir/f'{side}_{x}_{y}_washer.step'),note='SCW-YAW-PLATE-WASHER-01 A-candidate; comparison only')
  else:
   add(f'{side}_plate_{i}_washer',cyl(3,.9,91).cut(cyl(1.15,.9,91)),note='SCW-SOLE-SPACER-01 nominal rigid-washer candidate')
  add(f'{side}_plate_{i}_nut',cyl(2.829,1.2,91.9).cut(cyl(1,1.2,91.9)),note='PTS A56202 circumcircle envelope, not square CAD')
assy.save(str(a.out/'yaw_support_candidate.step'))
report={'scope':__doc__,'parts':rows,'part_count':len(rows),'solid_count':sum(r['solids'] for r in rows),'omitted':['servo and horn hardware','case PHS M2x8 TAP screws','rear-plate-to-body corner hardware','legs','battery/electronics/harness','tools'],'manufacturing_release':False,'full_interference_verified':False,'strength_verified':False}
(a.out/'inventory.json').write_text(json.dumps(report,indent=2)+'\n')
if a.moments:
 (a.out/'geometric_moments.json').write_text(json.dumps({'coordinate_frame':'assembly CAD origin, axes unchanged; mm converted to m','density_assigned':False,'analytic_translated_box_check':True,'parts':moments,'manufacturing_release':False},indent=2)+'\n')
print(json.dumps({k:report[k] for k in ['part_count','solid_count','manufacturing_release']}))
