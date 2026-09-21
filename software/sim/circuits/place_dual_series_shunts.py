"""Four-resistor layout candidate and explicit interconnect-only resistance estimate."""
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
source=Path('board/power/placement_revA/power_placement.kicad_pcb');s=source.read_text().rstrip()[:-1]
parts=[]
for side,center,n in [('L',70,3),('R',110,6)]:
 labels=[f'{side}_SHUNT_{x}' for x in ['HIGH','MID','LOW']]
 for i,label in enumerate(labels):s+=f'\n(net {n+i} "{label}")'
 for j,x in enumerate([center-3.6,center+3.6]):
  s+=f'\n(footprint "WSLF2512_candidate" (layer "F.Cu") (at {x} 62.5) (attr smd) (fp_text reference "R_SENSE_{side}{j+1}" (at 0 3) (layer "F.SilkS") (effects (font (size 1 1) (thickness .15)))) (fp_text value "4m" (at 0 -3) (layer "F.Fab") (effects (font (size 1 1) (thickness .15))))'
  for k,dx in enumerate([-2.6,2.6]):
   s+=f'\n(pad "{k+1}" smd rect (at {dx} 0) (size 1.8 3.4) (layers "F.Cu" "F.Paste" "F.Mask") (net {n+j+k} "{labels[j+k]}"))'
  s+='\n)';parts.append({'reference':f'R_SENSE_{side}{j+1}','center_mm':[x,62.5]})
 def segment(x1,y1,x2,y2,w,net):return f'\n(segment (start {x1} {y1}) (end {x2} {y2}) (width {w}) (layer "F.Cu") (net {net}))'
 s+=segment(center-1,62.5,center+1,62.5,3.4,n+1)
 for sign,net in [(-1,n),(1,n+2)]:
  s+=segment(center+sign*6.2,62.5,center+sign*10,62.5,2,net)
  s+=segment(center+sign*5.4,62.5,center+sign*5.4,58.5,.2,net)
s+='\n)\n'
# Explicit comparison inputs, not PCB fabrication specifications or validated material properties.
rho20=1.724e-8;alpha=.00393;temp=150;length=.002;width=.0034;thickness=35e-6
wire=rho20*(1+alpha*(temp-20))*length/(width*thickness)
up=Path('validation/shunt_stability_comparison_v1/report.json');r=json.loads(up.read_text())['rows'][1]
remaining=r['remaining_positive_error_V']-4.917*wire
report={'source_sha256':{str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in [source,up]},
 'parts':parts,'pad_dimensions_mm':{'length':1.8,'width':3.4,'gap':3.4},
 'interconnect_model':{'rho20_ohm_m':rho20,'alpha_per_K':alpha,'temperature_C':temp,'length_m':length,'width_m':width,'copper_thickness_m':thickness,'resistance_ohm':wire},
 'remaining_error_after_trace_only_V':remaining,'trace_only_screen_pass':remaining>0,
 'limits':['Uniform rectangular copper segment only; pad spreading terminal pickup solder contacts and etch tolerances excluded.',
 'Copper parameters and thickness are comparison inputs, not manufacturing guarantees.',
 'At temperature150C this is resistance calculation, not proof of acceptable board/component temperature.',
 'Controller MOSFET connectors and most circuit not placed; outer stubs unconnected.',
 'Two-resistor alternative; current revM protection design unchanged.'],
 'layout_qualified':False,'manufacturing_release':False}
a.out.mkdir(parents=True,exist_ok=False);(a.out/'placement.kicad_pcb').write_text(s);(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'wire_mOhm':wire*1000,'remaining_mV':remaining*1000}))
