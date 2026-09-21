"""Replace eight yaw mount nut collision envelopes; preserve the other 44 solids.

The new rotational envelopes are not mass or actual bearing-surface models.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import cadquery as cq
from OCP.GProp import GProp_GProps
from OCP.BRepGProp import BRepGProp

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--out', type=Path, required=True)
a = p.parse_args()
a.out.mkdir(parents=True, exist_ok=False)
base = Path('validation/yaw_integrated_candidate_v4')
specpath = Path('docs/prototype/mechanical/yaw_hex_nut/candidate.json')
spec = json.loads(specpath.read_text())
inv = json.loads((base/'inventory.json').read_text())
mom = json.loads((base/'geometric_moments.json').read_text())
solids = cq.importers.importStep(str(base/'yaw_support_candidate.step')).val().Solids()
assert len(solids) == len(inv['parts']) == len(mom['parts']) == 52
plan = {'source_sha256': {str(f): hashlib.sha256(f.read_bytes()).hexdigest() for f in [specpath,base/'inventory.json',base/'geometric_moments.json',base/'yaw_support_candidate.step']},
        'question': 'Can eight class-6 hex-nut nominal rotational envelopes replace the thin square nuts without modifying screw diameter or leg/body geometry?',
        'stop': 'One substitution at original axes and washer-top Z; check all 1326 pairs. No material or preload sweep.',
        'model': 'Cylinder of radius across-flats/sqrt(3), catalog maximum height, nominal M2 bore. No chamfers or threads.',
        'qualification': False}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
assy = cq.Assembly(name='yaw_support_candidate')
changed=[]
for item,prop,solid in zip(inv['parts'],mom['parts'],solids):
    assert item['name']==prop['name'] and abs(item['volume_mm3']-solid.Volume())<1e-5
    name=item['name']
    if '_plate_' in name and name.endswith('_nut'):
        b=solid.BoundingBox();x=(b.xmin+b.xmax)/2;y=(b.ymin+b.ymax)/2;z=b.zmin
        radius=spec['across_flats_catalog_mm']/math.sqrt(3)
        height=spec['height_max_catalog_mm']
        new=cq.Solid.makeCylinder(radius,height,cq.Vector(x,y,z)).cut(cq.Solid.makeCylinder(1,height,cq.Vector(x,y,z)))
        assert new.isValid() and len(new.Solids())==1
        # Rotation-independent lateral envelope is narrower than the old square envelope.
        assert radius < b.xlen/2
        changed.append({'name':name,'old_top_z_mm':b.zmax,'new_top_z_mm':z+height,'nominal_screw_tip_protrusion_mm':98-(z+height),'mass_delta_g':None})
        solid=new
        item.update(volume_mm3=solid.Volume(),source=str(specpath),source_sha256=hashlib.sha256(specpath.read_bytes()).hexdigest(),note='Bossard 1088211 nominal rotational collision envelope; not bearing/physical mass')
        gp=GProp_GProps();BRepGProp.VolumeProperties_s(solid.wrapped,gp);c=gp.CentreOfMass();i=gp.MatrixOfInertia()
        prop.update(volume_mm3=solid.Volume(),mass_kg_per_density_kg_m3=solid.Volume()*1e-9,com_assembly_m=[c.X()*.001,c.Y()*.001,c.Z()*.001],inertia_com_kg_m2_per_density_kg_m3=[[i.Value(j,k)*1e-15 for k in range(1,4)] for j in range(1,4)],use_for_material_mass=False,restriction='Rotational collision envelope, not physical nut mass or bearing shape')
    assy.add(solid,name=name)
assert len(changed)==8
assy.save(str(a.out/'yaw_support_candidate.step'))
inv['scope']=__doc__;inv['comparison_base']=str(base)
(a.out/'inventory.json').write_text(json.dumps(inv,indent=2)+'\n')
(a.out/'geometric_moments.json').write_text(json.dumps(mom,indent=2)+'\n')
account=json.loads((base/'change_accounting.json').read_text())
account['source_sha256'].update(plan['source_sha256'])
account['changed_parts']+=changed
account['unchanged_names']=[n for n in account['unchanged_names'] if n not in {r['name'] for r in changed}]
account['delta_mass_g_excludes_replaced_nuts']=account.pop('delta_mass_g')
account['delta_first_moment_kg_m_excludes_replaced_nuts']=account.pop('delta_first_moment_kg_m')
account['delta_inertia_about_assembly_origin_kg_m2_excludes_replaced_nuts']=account.pop('delta_inertia_about_assembly_origin_kg_m2')
account['limits']+=['Eight nut masses and inertias unresolved; aggregate deltas exclude their replacement.']
(a.out/'change_accounting.json').write_text(json.dumps(account,indent=2)+'\n')
(a.out/'nut_replacement_report.json').write_text(json.dumps({'changes':changed,'unchanged_from_v4_parts':44,'manufacturing_release':False},indent=2)+'\n')
print(json.dumps({'replaced_nuts':len(changed),'unchanged_from_v4':44,'new_top_z_mm':changed[0]['new_top_z_mm']}))
