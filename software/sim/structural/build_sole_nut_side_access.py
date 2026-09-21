"""Candidate removable nut access; preserve bearing floor, no strength claim."""
from pathlib import Path
import argparse,json,hashlib
import cadquery as cq
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
plan={'question':'Can a maximum-envelope nut be inserted from positive X without opening the bearing floor?','opening_mm':{'width_y':4.4,'height_z':1.8,'bottom_z':-14.2,'from_x':35,'to_x':44},'criteria':{'valid_single_solid':True,'sampled_overlap_max_mm3':.01},'stop_condition':'One geometry, two sides, nine insertion poses; retain failure rather than sweeping dimensions','limitations':['Nominal geometry only; print tolerance and tool grip not verified','Nut retained by installed screw only; loose nut can exit opening','Side wall removal changes strength; old FE results do not qualify this candidate']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');rows=[];hashes={}
for side,cy in [('left',6),('right',-6)]:
 root=Path('validation/sole_wide_seat_v1/cad')
 paths={'yoke':root/f'{side}_yoke.step','nut':root/f'{side}_nut.step','boot':Path(f'validation/boot_low_head_candidate_v1/cad/{side}_boot_shell.step')}
 parts={k:cq.importers.importStep(str(v)).val() for k,v in paths.items()};hashes.update({str(v):hashlib.sha256(v.read_bytes()).hexdigest() for v in paths.values()})
 y=parts['yoke'].cut(cq.Solid.makeBox(9,4.4,1.8,cq.Vector(35,cy-2.2,-14.2))).clean()
 valid=y.isValid() and len(y.Solids())==1
 cq.exporters.export(y,str(a.out/f'{side}_yoke.step'))
 samples=[]
 for dx in range(8,-1,-1):
  n=parts['nut'].translate((dx,0,0));samples.append({'dx_mm':dx,'nut_yoke_overlap_mm3':n.intersect(y).Volume(),'nut_boot_overlap_mm3':n.intersect(parts['boot']).Volume()})
 rows.append({'side':side,'valid_single_solid':valid,'removed_volume_mm3':parts['yoke'].Volume()-y.Volume(),'samples':samples,'nominal_path_gate':valid and all(max(s['nut_yoke_overlap_mm3'],s['nut_boot_overlap_mm3'])<=.01 for s in samples)})
r={'rows':rows,'source_sha256':hashes,'assembly_with_screw_removed_only':True,'strength_verified':False,'manufacturing_release':False};(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
