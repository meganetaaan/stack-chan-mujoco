"""Place two alternative series-clamp shunts with separated current and sense trace stubs."""
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
source=Path('board/power/placement_revA/power_placement.kicad_pcb');base=source.read_text().rstrip();assert base.endswith(')')
base=base[:-1];extra=[];rows=[]
# Manufacturer recommended pads for 7..10 mOhm: a=1.65, b=3.18, l=4.06 mm gap.
for side,x,n in [('L',70,3),('R',110,5)]:
 y=62.5
 for i,label in [(n,f'{side}_SHUNT_HIGH'),(n+1,f'{side}_SHUNT_LOW')]:extra.append(f'(net {i} "{label}")')
 extra.append(f'(footprint "WSLP2512_7to10mOhm_candidate" (layer "F.Cu") (at {x} {y}) (attr smd) (fp_text reference "R_SENSE_{side}" (at 0 3) (layer "F.SilkS") (effects (font (size 1 1) (thickness .15)))) (fp_text value "8.2m" (at 0 -3) (layer "F.Fab") (effects (font (size 1 1) (thickness .15))))')
 for pad,dx,net,label in [(1,-2.855,n,f'{side}_SHUNT_HIGH'),(2,2.855,n+1,f'{side}_SHUNT_LOW')]:
  extra.append(f'(pad "{pad}" smd rect (at {dx} 0) (size 1.65 3.18) (layers "F.Cu" "F.Paste" "F.Mask") (net {net} "{label}"))')
 extra.append(')')
 for sign,net in [(-1,n),(1,n+1)]:
  pad_x=x+sign*2.855
  # Current arrives from outside; sense exits perpendicular at inner pad edge.
  sense_x=x+sign*2.13
  extra.append(f'(segment (start {pad_x} {y}) (end {x+sign*8} {y}) (width 2) (layer "F.Cu") (net {net}))')
  extra.append(f'(segment (start {sense_x} {y}) (end {sense_x} 58.5) (width .2) (layer "F.Cu") (net {net}))')
 rows.append({'side':side,'center_mm':[x,y],'pad_size_mm':[1.65,3.18],'pad_gap_mm':4.06,'power_trace_width_mm':2,'sense_trace_width_mm':.2})
# The .2/2 mm widths and inner-edge pickup are design proposals, not current/thermal qualified.
a.out.mkdir(parents=True,exist_ok=True);(a.out/'placement.kicad_pcb').write_text(base+'\n'+'\n'.join(extra)+'\n)\n')
(a.out/'report.json').write_text(json.dumps({'source_sha256':{str(source):hashlib.sha256(source.read_bytes()).hexdigest()},'placements':rows,
 'datasheet':'https://www.vishay.com/docs/30122/wslp.pdf','status':'Alternative LT4363 layout study, not current revM protection board',
 'limits':['Trace stubs have open ends; controller MOSFET connectors and remaining circuit unplaced.', 'Two-terminal shunt: Kelvin trace separation does not remove shared pad/terminal resistance.', 'Trace width and pad pickup need electrical/thermal extraction and assembly review.', 'No whole-board DRC or manufacturing release.'], 'manufacturing_release':False},indent=2)+'\n')
