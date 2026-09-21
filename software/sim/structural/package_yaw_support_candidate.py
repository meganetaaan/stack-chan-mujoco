"""Package the current yaw-support candidate without claiming assembly qualification."""
import argparse,hashlib,json
from pathlib import Path
import cadquery as cq
ROOT=Path(__file__).resolve().parents[3];p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
assy=cq.Assembly(name='yaw_support_candidate');rows=[]
def add(name,s,source=None,note='nominal geometry'):
 assert s.isValid()
 assy.add(s,name=name);r={'name':name,'solids':len(s.Solids()),'volume_mm3':s.Volume(),'source':source,'note':note}
 if source:r['source_sha256']=hashlib.sha256((ROOT/source).read_bytes()).hexdigest()
 rows.append(r)
def read(name,path,shift=None,note='nominal geometry'):
 s=cq.importers.importStep(str(ROOT/path)).val()
 if shift:s=s.translate(shift)
 add(name,s,path,note)
read('body_shroud','validation/yaw_tool_access_v1/body_shroud.step')
read('rear_plate','validation/rear_joint_assembly_development_v1/rear_joint_inset2_v1/rear_structural_plate.step')
for side,cy in [('left',26),('right',-26)]:
 for name in ['yaw_fixed_support','threaded_backing_plate']:
  read(side+'_'+name,f'validation/yaw_backing_keeper_v2/{side}_{name}.step')
 read(side+'_mount_plate',f'validation/yaw_metal_seat_v4/{side}_mount_plate.step')
 for z in [64,76]:read(f'{side}_{z}_keeper',f'validation/yaw_backing_keeper_v2/{side}_{z}_keeper_envelope.step',note='NBK SLH-M2-10 nominal; thread overlap intentional')
 for i in range(4):
  for name in ['bolt','rear_washer']:read(f'{side}_rear_{i}_{name}',f'validation/inset_yaw_assembly_development_v1/inset_fasteners_staged_v2/{side}_{i}_{name}.step',(-.2,0,0),'M3 hardware envelope moved to 2 mm rear plate; inner nut/washer replaced by threaded plate')
 for i,(x,y) in enumerate(( (x,y) for x in [-34,8.1] for y in [cy-10,cy+10])):
  def cyl(r,h,z):return cq.Solid.makeCylinder(r,h,cq.Vector(x,y,z))
  add(f'{side}_plate_{i}_screw',cyl(1.9,1.3,86.7).fuse(cyl(1,10,88)),note='NBK SLH-M2-10 nominal envelope')
  add(f'{side}_plate_{i}_washer',cyl(3,.9,91).cut(cyl(1.15,.9,91)),note='SCW-SOLE-SPACER-01 nominal rigid-washer candidate')
  add(f'{side}_plate_{i}_nut',cyl(2.829,1.2,91.9).cut(cyl(1,1.2,91.9)),note='PTS A56202 circumcircle envelope, not square CAD')
assy.save(str(a.out/'yaw_support_candidate.step'))
report={'scope':__doc__,'parts':rows,'part_count':len(rows),'solid_count':sum(r['solids'] for r in rows),'omitted':['servo and horn hardware','case PHS M2x8 TAP screws','rear-plate-to-body corner hardware','legs','battery/electronics/harness','tools'],'manufacturing_release':False,'full_interference_verified':False,'strength_verified':False}
(a.out/'inventory.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ['part_count','solid_count','manufacturing_release']}))
