"""Assemble exact selected foot candidate sources without manufacturing approval."""
import argparse,json,hashlib
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False);rows=[]
for side in ['left','right']:
 assembly=cq.Assembly(name=side+'_foot_candidate')
 for part in ['boot','yoke','sole','spacer','screw','nut']:
  if part=='boot':src=Path(f'validation/boot_low_head_candidate_v1/cad/{side}_boot_shell.step')
  elif part in ['yoke','screw','nut']:src=Path(f'validation/sole_external_nut_v1/{side}_{part}.step')
  else:src=Path(f'validation/sole_wide_seat_v1/cad/{side}_{part}.step')
  shape=cq.importers.importStep(str(src)).val();assert shape.isValid() and len(shape.Solids())==1
  assembly.add(shape,name=side+'_'+part)
  rows.append({'side':side,'part':part,'source':str(src),'sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'volume_mm3':shape.Volume(),'valid_single_solid':True})
 cq.exporters.export(assembly.toCompound(),str(a.out/f'{side}_foot_candidate.step'))
r={'scope':'Six-part nominal assembly per foot; no servo, horn fasteners or harness','parts':rows,'spacer_note':'Nominal sharp-edge spacer; rounded/minimum tolerance analysis geometry is not the manufacturing nominal','manufacturing_release':False,'motion_and_strength_verified':False};(a.out/'inventory.json').write_text(json.dumps(r,indent=2)+'\n');print('Packaged 12 valid solids from explicit sources')
