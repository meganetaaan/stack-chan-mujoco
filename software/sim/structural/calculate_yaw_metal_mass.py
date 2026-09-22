"""Nominal mass properties of selected metal plates only; does not modify frozen robot."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
root=Path(__file__).resolve().parents[3]
inputs=['validation/yaw_geometric_moments_v1/geometric_moments.json','validation/base_mass_provenance_development_v1/report.json','board/mechanical/prototype/yaw_support_candidate/revA/inventory.json']
d,old,inventory=[json.loads((root/r).read_text()) for r in inputs]
provenance=json.loads((root/'validation/yaw_geometric_moments_v1/report.json').read_text())
for rel,expected in provenance['source_sha256'].items():
    assert hashlib.sha256((root/rel).read_bytes()).hexdigest()==expected, 'Stale geometric moment source: '+rel
# Preserve nominal source identity: masses must not refer to a different CAD revision.
volumes={p['name']:p['volume_mm3'] for p in inventory['parts']}
rows=[]
for part in d['parts']:
    n=part['name']
    if n=='rear_plate' or n.endswith('threaded_backing_plate'):material,rho='A5052P-H34',2680
    elif n.endswith('mount_plate'):material,rho='SUS304',7930
    else:continue
    assert part['use_for_material_mass'] and abs(part['volume_mm3']-volumes[n])<1e-6
    rows.append({'name':n,'material_candidate':material,'density_reference_kg_m3':rho,'mass_kg':part['mass_kg_per_density_kg_m3']*rho,'com_assembly_m':part['com_assembly_m'],'inertia_com_kg_m2':(np.array(part['inertia_com_kg_m2_per_density_kg_m3'])*rho).tolist()})
assert len(rows)==5
mass=sum(r['mass_kg'] for r in rows)
com=sum(r['mass_kg']*np.array(r['com_assembly_m']) for r in rows)/mass
I=np.zeros((3,3))
for r in rows:
    offset=np.array(r['com_assembly_m'])-com
    I+=np.array(r['inertia_com_kg_m2'])+r['mass_kg']*(np.dot(offset,offset)*np.eye(3)-np.outer(offset,offset))
assert min(np.linalg.eigvalsh(I))>0
rear=next(r for r in rows if r['name']=='rear_plate')
report={'parts':rows,'aggregate_metal_only':{'mass_kg':mass,'com_assembly_m':com.tolist(),'inertia_com_kg_m2':I.tolist()},'rear_plate_only_delta_from_frozen_cover_kg':rear['mass_kg']-old['components']['rear_cover']['mass_kg'],'reference_density_sources':{'A5052':'https://www.izumi-metal.co.jp/cms/wp-content/uploads/2025/06/UACJ_UEX_type.pdf','SUS304':'https://www.nipponsteel.com/assets/pdf/product/grade/nssc_series/ferrite/S007_SPEC36.pdf'},'source_sha256':{r:hashlib.sha256((root/r).read_bytes()).hexdigest() for r in inputs},'limits':['reference density and nominal geometry, not guaranteed maximum mass','excludes printed parts, washers, screws, nuts, wires and electronics','thread pilot CAD omits removed tap material and final chamfers','metal-only COM is not body or robot COM'],'robot_model_updated':False,'manufacturing_release':False}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'metal_total_g':mass*1000,'rear_delta_g':report['rear_plate_only_delta_from_frozen_cover_kg']*1000,'parts':[(r['name'],r['mass_kg']*1000) for r in rows]},indent=2))
