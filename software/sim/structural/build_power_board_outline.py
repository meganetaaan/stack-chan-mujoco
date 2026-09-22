"""Create provisional PCB outline/mount keepouts, not a routed power board."""
import argparse,json
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
holes=[(u,v) for u in (4,76) for v in (4,21)]
board=cq.Solid.makeBox(1.6,80,25,cq.Vector(0,-40,99))
for u,v in holes:board=board.cut(cq.Solid.makeCylinder(1.2,1.6,cq.Vector(0,u-40,124-v),cq.Vector(1,0,0)))
assert board.isValid() and len(board.Solids())==1
cq.exporters.export(board,str(a.out/'board.step'))
lines=['(kicad_pcb (version 20221018) (generator pcbnew)','(general (thickness 1.6))','(paper "A4")','(layers (0 "F.Cu" signal) (31 "B.Cu" signal) (36 "B.SilkS" user "b.silkscreen") (37 "F.SilkS" user "f.silkscreen") (44 "Edge.Cuts" user))','(setup (pad_to_mask_clearance 0))','(net 0 "")']
for x1,y1,x2,y2 in [(50,50,130,50),(130,50,130,75),(130,75,50,75),(50,75,50,50)]:lines.append(f'(gr_line (start {x1} {y1}) (end {x2} {y2}) (stroke (width 0.05) (type default)) (layer "Edge.Cuts"))')
for i,(u,v) in enumerate(holes,1):
 x,y=50+u,50+v
 lines.append(f'(footprint "MountingHole_2.4mm_candidate" (layer "F.Cu") (at {x} {y}) (attr exclude_from_pos_files exclude_from_bom) (fp_text reference "H{i}" (at 0 -2) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15)))) (pad "" np_thru_hole circle (at 0 0) (size 2.4 2.4) (drill 2.4) (layers "*.Cu" "*.Mask")))')
 lines.append(f'(zone (net 0) (net_name "") (layers "F.Cu" "B.Cu") (hatch edge 0.5) (keepout (tracks not_allowed) (vias not_allowed) (pads not_allowed) (copperpour not_allowed) (footprints not_allowed)) (polygon (pts (xy {x-3} {y-3}) (xy {x+3} {y-3}) (xy {x+3} {y+3}) (xy {x-3} {y+3}))))')
lines.append(')');(a.out/'power_outline.kicad_pcb').write_text('\n'.join(lines)+'\n')
(a.out/'dimensions.json').write_text(json.dumps({'outline_mm':[80,25],'thickness_mm':1.6,'holes_local_uv_mm':holes,'drill_mm':2.4,'keepout_square_mm':6,'coordinate_mapping':'local(u,v) -> robot(x,y,z)=(0..1.6,u-40,124-v)','remaining_planar_area_excluding_mount_squares_mm2':80*25-4*36,'assumptions':['M2 clearance-hole proposal, not final fastener selection','6mm square keepout is a design reservation','No connector, routing, support or thermal design included'],'manufacturing_release':False},indent=2)+'\n')
print('Outline and four mounting reservations exported')
