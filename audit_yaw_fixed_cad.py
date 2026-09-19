"""Check corrected yaw case intersections against the available fixed CAD parts."""
import sys,json,argparse,hashlib
from pathlib import Path
import cadquery as cq
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--cad-design',type=Path,required=True)
parser.add_argument('--design',type=Path,required=True)
parser.add_argument('--out',type=Path,required=True)
a=parser.parse_args()
if a.out.exists():parser.error('new output required')
sys.path[:0]=[str((a.cad_design/'cad').resolve()),str((a.cad_design/'src').resolve())]
from build import build
p=a.design
parts={x.name:x.shape for x in build() if x.link=='base' and x.role!='visual'}
for name in list(parts):
 if 'hip_roll_motor' in name or 'fixed_roll_cradle' in name:del parts[name]
 if name=='TTL_interface':parts[name]=parts[name].translate((0,0,12))
for f in (p/'cad').glob('*.step'):
 if 'coupler' not in f.stem and 'cradle' not in f.stem and 'horn' not in f.stem:parts[f.stem]=cq.importers.importStep(str(f)).val()
result=[]
for side in ['left','right']:
 name=side+'_yaw_motor_case';case=parts[name]
 for other,shape in parts.items():
  if other==name:continue
  vol=case.intersect(shape).Volume()
  if vol>1e-6:result.append({'motor':name,'other':other,'overlap_mm3':vol})
out={'scope':'CAD intersection of corrected yaw case with rebuilt base parts and generated tray/supports; battery accessories outside these inputs not covered','overlaps':result,'checked_parts':sorted(parts)}
out['source_sha256']={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in [Path(__file__),a.cad_design/'cad/build.py',a.cad_design/'cad/r4_geometry.py',*sorted((p/'cad').glob('*.step'))]}
a.out.parent.mkdir(parents=True,exist_ok=True)
a.out.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
