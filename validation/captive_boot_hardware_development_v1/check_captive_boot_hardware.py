"""Check nominal low-head screw/nut envelopes and print-pause nut insertion."""
import argparse,hashlib,json
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[3]
if a.out.exists():p.error('new output required')
a.out.mkdir(parents=True)
paths={s:{'boot':root/f'validation/boot_low_head_candidate_v1/cad/{s}_boot_shell.step','sole':root/f'validation/boot_low_head_candidate_v1/cad/{s}_sole_TPU.step','yoke':root/f'validation/native_horn_yoke_development_v1/v4/{s}_foot_yoke.step'} for s in ('left','right')}
plan={'scope':__doc__,'screw_envelope_mm':{'head_radius':1.9,'head_z':[-20.3,-19],'shaft_radius':1,'shaft_z':[-19,-13]},'nut_envelope_mm':{'width':4,'thickness':1.2,'z':[-14.6,-13.4]},'print_pause_z_mm':-12.8,'nut_insertion_bottom_start_z_mm':40,'overlap_max_mm3':.01,'source_sha256':{str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for row in paths.values() for f in row.values()},'limitations':['Nominal catalog envelopes only, not supplier CAD or tolerance extremes.','No helical thread, head fillet, tightening torque, thread strength or printer/tool-head simulation.','Print-pause cut assumes +Z build orientation and exactly planned layer height.']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');rows=[]
printed_halfspace=cq.Workplane('XY').box(300,300,200).val().translate((0,0,-112.8))
for side,files in paths.items():
 shapes={k:cq.importers.importStep(str(f)).val() for k,f in files.items()};printed=shapes['boot'].intersect(printed_halfspace);sign=1 if side=='left' else -1
 for x in (-34,36):
  for y in (sign*6-20.5,sign*6+20.5):
   shaft=cq.Solid.makeCylinder(1,6,cq.Vector(x,y,-19));head=cq.Solid.makeCylinder(1.9,1.3,cq.Vector(x,y,-20.3));screw=shaft.fuse(head)
   nut=cq.Workplane('XY').box(4,4,1.2).val().translate((x,y,-14)).cut(cq.Solid.makeCylinder(1,1.4,cq.Vector(x,y,-14.7)))
   sweep=cq.Workplane('XY').box(4,4,55.8).val().translate((x,y,13.3))
   # Entire translating nut is enclosed by this box: bottom -14.6 to top 41.2.
   insertion=sweep.intersect(printed).Volume()
   overlaps={f'{hw}_{name}':solid.intersect(shape).Volume() for hw,solid in [('screw',screw),('nut',nut)] for name,shape in shapes.items()}
   rows.append({'side':side,'xy_mm':[x,y],'overlap_mm3':overlaps,'insertion_swept_overlap_mm3':insertion,'passed':insertion<=.01 and all(v<=.01 for v in overlaps.values())})
   for name,solid in [('screw',screw),('nut',nut)]:cq.exporters.export(solid,str(a.out/f'{side}_{x}_{y}_{name}.step'))
(a.out/'report.json').write_text(json.dumps({'rows':rows,'all_nominal_checks_pass':all(r['passed'] for r in rows),'manufacturing_release':False},indent=2)+'\n');print(json.dumps(rows,indent=2))
