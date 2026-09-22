"""Continuous nominal translation via swept boundary faces of stationary obstacles."""
import hashlib,itertools,json
from pathlib import Path
import cadquery as cq
from OCP.BRepPrimAPI import BRepPrimAPI_MakePrism
from OCP.gp import gp_Vec
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'validation/insert_carrier_removal_v1';OUT.mkdir(exist_ok=True)
src=ROOT/'validation/serviceable_torso_v2';r=json.loads((src/'report.json').read_text());solids=cq.importers.importStep(str(src/'assembly.step')).val().Solids()
assert len(solids)==len(r['parts'])
parts={row['name']:s for row,s in zip(r['parts'],solids)}
for row,s in zip(r['parts'],solids):assert abs(row['volume_mm3']-s.Volume())<1e-5
moving={n:s for n,s in parts.items() if n=='new_carrier' or n.endswith('_insert') or n=='Tab5'}
assert len(moving)==6, list(moving)
removed={f'new_{sign}_{z}_screw' for sign in [-1,1] for z in [88,112]}
assert removed<=parts.keys()
fixed={n:s for n,s in parts.items() if n not in moving and n not in removed}
travel=40.
plan={'translation_mm':[travel,0,0],'removed_before_move':sorted(removed),'moving':sorted(moving),
 'criteria':'No nominal volume overlap >0.01mm3 over continuous translation; geometry errors remain unresolved',
 'method':'Intersect moving solids at initial pose with each stationary solid swept backward by40mm, represented by original solid plus prisms of all its boundary faces',
 'limits':['No cables, hand, tool, deformation or tolerances','Simplified Tab5 envelope and installed insert approximation','Tab5-to-carrier screws absent']}
(OUT/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
# Independent analytic check: a unit cube translated by two units sweeps a 3x1x1 box.
cube=cq.Workplane('XY').box(1,1,1).val();sweep=cube
for face in cube.Faces():
 prism=cq.Shape.cast(BRepPrimAPI_MakePrism(face.wrapped,gp_Vec(-2,0,0)).Shape())
 if prism.Solids() and prism.Volume()>1e-8:sweep=sweep.fuse(prism)
expected=cq.Workplane('XY').box(3,1,1).translate((-1,0,0)).val()
analytic_difference=sweep.cut(expected).Volume()+expected.cut(sweep).Volume()
assert analytic_difference<1e-8
flags=[];errors=[];pruned=0;tested=0;max_observed=0.
for fn,fs in fixed.items():
 b=fs.BoundingBox();box=cq.Workplane('XY').box(b.xlen+travel,b.ylen,b.zlen).translate(((b.xmin+b.xmax-travel)/2,(b.ymin+b.ymax)/2,(b.zmin+b.zmax)/2)).val()
 candidates=[]
 for mn,ms in moving.items():
  if ms.intersect(box).Volume()>.01:candidates.append((mn,ms))
  else:pruned+=1
 if not candidates:continue
 swept=[fs]
 for i,face in enumerate(fs.Faces()):
  try:
   shape=cq.Shape.cast(BRepPrimAPI_MakePrism(face.wrapped,gp_Vec(-travel,0,0)).Shape())
   if shape.Volume()>1e-8 and shape.Solids():
    if not shape.isValid():raise ValueError('invalid face prism')
    swept.append(shape)
  except Exception as exc:errors.append({'part':fn,'face':i,'error':str(exc)})
 for mn,ms in candidates:
  tested+=1
  maximum=max(ms.intersect(s).Volume() for s in swept)
  max_observed=max(max_observed,maximum)
  if maximum>.01:flags.append({'moving':mn,'fixed':fn,'max_single_sweep_piece_overlap_mm3':maximum})
result={'analytic_cube_sweep_difference_mm3':analytic_difference,'max_single_piece_overlap_mm3':max_observed,'moving_count':len(moving),'fixed_count':len(fixed),'broad_phase_pruned_pairs':pruned,
 'detailed_pairs':tested,'overlap_flags':flags,'geometry_errors':errors,
 'nominal_path_clear':not flags and not errors,'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [src/'assembly.step',src/'report.json']},
 'manufacturing_release':False,'service_procedure_qualified':False}
(OUT/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
