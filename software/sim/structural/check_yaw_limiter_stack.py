"""Check necessary sleeve seating geometry without inventing print allowables."""
import argparse
import hashlib
import json
from pathlib import Path

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--out',type=Path,required=True)
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
ref=Path('validation/yaw_joint_interfaces_v4/report.json')
v4=Path('validation/yaw_integrated_candidate_v4/inventory.json')
v5=Path('validation/yaw_integrated_candidate_v5/inventory.json')
planpath=Path('validation/yaw_compression_limiter_gate_v1/plan.json')
old={r['name']:r for r in json.loads(v4.read_text())['parts']}
new={r['name']:r for r in json.loads(v5.read_text())['parts']}
interfaces={r['name']:r for r in json.loads(ref.read_text())['rows']}
rows=[]
for side in ['left','right']:
    for suffix in ['mount_plate','yaw_fixed_support']:
        assert old[side+'_'+suffix]==new[side+'_'+suffix]
    plate=interfaces[side+'_plate_shelf']['z_mm']
    for i in range(4):
        washer=f'{side}_plate_{i}_washer'
        assert old[washer]==new[washer]
        top=interfaces[f'{side}_plate_{i}_shelf_washer']['z_mm']
        thickness=top-plate
        assert thickness>0
        # Published L=2 +/-0.1; no manufacturing tolerance invented for the shelf.
        shortest,longest=1.9,2.1
        rows.append({'joint':f'{side}_plate_{i}','nominal_plastic_thickness_mm':thickness,
                     'long_spacer_gap_at_nominal_shelf_mm':max(0,longest-thickness),
                     'short_spacer_compression_to_seat_at_nominal_shelf_mm':max(0,thickness-shortest),
                     'short_spacer_geometric_compression_strain':max(0,thickness-shortest)/thickness,
                     'always_clamps_even_nominal_shelf':longest<=thickness})
report={'source_sha256':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in [ref,v4,v5,planpath]},
        'rows':rows,'decision':'stock_spacer_not_drop_in_qualified',
        'limits':['Shelf thickness is nominal; actual print thickness and flatness are unknown.',
                  'Strain is only geometric displacement needed to reach the spacer, not material acceptance.',
                  'Metal compression, face indentation and bending are omitted.',
                  'Pipe-spacer axial load rating is not established; not a qualified compression limiter.',
                  'No holes, formal BOM, preload or acceptance limits were changed.'],
        'manufacturing_release':False}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'joints':len(rows),'all_nominal_thickness_mm':sorted({r['nominal_plastic_thickness_mm'] for r in rows}),
                  'any_always_clamps':any(r['always_clamps_even_nominal_shelf'] for r in rows)},indent=2))
