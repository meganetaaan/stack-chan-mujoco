"""Check whether installed lock hardware prevents rigid-holder axial displacement."""
import argparse,json,hashlib
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
rows=[];hashes={}
for side in ['left','right']:
 paths={'holder':Path(f'validation/rigid_sole_heads_v1/{side}_holder_envelope.step'),'yoke':Path(f'validation/rigid_sole_keyhole_v1/{side}_yoke.step'),'boot':Path(f'validation/boot_low_head_candidate_v1/cad/{side}_boot_shell.step'),'screw':Path(f'validation/sole_external_nut_v1/{side}_screw.step'),'spacer':Path(f'validation/sole_wide_seat_v1/cad/{side}_spacer.step')}
 parts={n:cq.importers.importStep(str(f)).val() for n,f in paths.items()};hashes.update({str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in paths.values()})
 samples=[]
 for dz in [0,-.2,-.4,-.5,-.6,-.7]:
  s=parts['holder'].translate((0,0,dz));samples.append({'dz_mm':dz,'overlap_mm3':{n:s.intersect(t).Volume() for n,t in parts.items() if n!='holder'}})
 rows.append({'side':side,'samples':samples})
(a.out/'report.json').write_text(json.dumps({'rows':rows,'source_sha256':hashes,'manufacturing_release':False,'scope':'Nominal rigid translation with installed screw/spacer; no friction or adhesion credited, not a dynamics model'},indent=2)+'\n');print(json.dumps(rows))
