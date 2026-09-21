"""Continuous straight driver shaft approach with and without removable sole."""
import hashlib,json
from pathlib import Path
import cadquery as cq
ip=Path('board/mechanical/prototype/foot_candidate/revE/inventory.json')
dp=Path('docs/prototype/mechanical/boot_fasteners/driver_candidate.json')
inv=json.loads(ip.read_text());tool=json.loads(dp.read_text());rows=[]
for side,sign in [('left',1),('right',-1)]:
 shapes={r['part']:cq.importers.importStep(r['source']).val() for r in inv['parts'] if r['side']==side}
 for x in (-34,36):
  for y in (sign*6-20.5,sign*6+20.5):
   # Shaft swept from 40 mm below screw head to the entry plane.
   # Tool engagement into own screw is deliberately outside this test.
   shaft=cq.Solid.makeCylinder(tool['blade_diameter_mm']/2,tool['blade_length_mm'],cq.Vector(x,y,-20.3-tool['blade_length_mm']))
   overlaps={n:s.intersect(shaft).Volume() for n,s in shapes.items() if n!=f'boot_{x}_{y}_screw'}
   relevant={n:v for n,v in overlaps.items() if v>1e-8}
   removed={'holder','contact_layer'}
   rows.append({'side':side,'xy_mm':[x,y],'installed_sole_collisions_mm3':relevant,
    'sole_removed_collisions_mm3':{n:v for n,v in relevant.items() if n not in removed}})
report={'rows':rows,'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ip,dp)},
 'sole_removed_shaft_path_clear':all(not r['sole_removed_collisions_mm3'] for r in rows),
 'scope':'Local unmounted foot, straight shaft up to head entry plane; excludes own socket engagement, handle, hand, jig and full robot',
 'manufacturing_release':False,'torque_qualified':False}
Path('validation/boot_driver_access_v1/report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
