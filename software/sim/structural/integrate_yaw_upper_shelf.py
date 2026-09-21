"""Replace only two supports in v5 with the upper reinforcement comparison."""
import argparse,hashlib,json
from pathlib import Path
import cadquery as cq
from OCP.GProp import GProp_GProps
from OCP.BRepGProp import BRepGProp
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
base=Path('validation/yaw_integrated_candidate_v5');inv=json.loads((base/'inventory.json').read_text());mom=json.loads((base/'geometric_moments.json').read_text());solids=cq.importers.importStep(str(base/'yaw_support_candidate.step')).val().Solids()
assert len(solids)==len(inv['parts'])==len(mom['parts'])==52
files=[base/'inventory.json',base/'geometric_moments.json',base/'yaw_support_candidate.step'];changed=[];unchanged=[];assy=cq.Assembly(name='yaw_support_candidate')
for item,prop,solid in zip(inv['parts'],mom['parts'],solids):
 name=item['name'];assert name==prop['name'] and abs(item['volume_mm3']-solid.Volume())<1e-5
 if name in ['left_yaw_fixed_support','right_yaw_fixed_support']:
  path=Path('validation/yaw_upper_shelf_v1')/(name+'.step');files.append(path);new=cq.importers.importStep(str(path)).val();assert new.isValid() and len(new.Solids())==1
  changed.append({'name':name,'added_volume_mm3':new.Volume()-solid.Volume(),'actual_mass_delta_g':None})
  solid=new;item.update(volume_mm3=solid.Volume(),source=str(path),source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),note='Upper 2 mm reinforcement comparison; unqualified printed material')
  gp=GProp_GProps();BRepGProp.VolumeProperties_s(solid.wrapped,gp);c=gp.CentreOfMass();i=gp.MatrixOfInertia()
  prop.update(volume_mm3=solid.Volume(),mass_kg_per_density_kg_m3=solid.Volume()*1e-9,com_assembly_m=[c.X()*.001,c.Y()*.001,c.Z()*.001],inertia_com_kg_m2_per_density_kg_m3=[[i.Value(j,k)*1e-15 for k in range(1,4)] for j in range(1,4)])
 else:unchanged.append(name)
 assy.add(solid,name=name)
assert len(changed)==2 and len(unchanged)==50
assy.save(str(a.out/'yaw_support_candidate.step'));inv.update(scope=__doc__,comparison_base=str(base))
for name,data in [('inventory',inv),('geometric_moments',mom),('change_accounting',{'comparison_base':str(base),'changed_parts':changed,'unchanged_names':unchanged,'source_sha256':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},'limits':['Relative to v5 only; do not add to older aggregate mass twice.','Nut collision envelopes are not actual nut mass.','Density, full robot inertia and loads not updated.'],'manufacturing_release':False})]:
 (a.out/(name+'.json')).write_text(json.dumps(data,indent=2)+'\n')
print(json.dumps({'changed':changed,'unchanged':len(unchanged)}))
