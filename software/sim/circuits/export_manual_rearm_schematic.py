"""Native connectivity schematic with embedded generic pin symbols, not ERC-qualified."""
import argparse,csv,json,uuid
from pathlib import Path
from assembly_net_aliases import net_aliases
root=Path(__file__).resolve().parents[3]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--assembly');p.add_argument('--bom');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
c=json.loads((root/'schematics/power/manual_rearm_current.json').read_text());asm=json.loads((root/(a.assembly or c['assembly'])).read_text());bom={ref:r for r in csv.DictReader((root/(a.bom or c['quantity_bom'])).open()) for ref in r['references'].split()}
aliases=net_aliases(asm)
def uid(s):return str(uuid.uuid5(uuid.NAMESPACE_URL,'stackchan-revI-schematic/'+s))
def q(s):return json.dumps(s,ensure_ascii=False)
def effects(size=1):return f'(effects (font (size {size} {size})))'
sheet=uid('root');libs=[];instances=[];connections=[]
for index,part in enumerate(asm['parts']):
 ref=part['reference'];pins=list(part['pins']);n=len(pins);x=55+(index%7)*80;y=40+(index//7)*55;half=max(3.81,(n+1)*1.27)
 body=f'(symbol "{ref}_0_1" (rectangle (start -10.16 {half}) (end 10.16 {-half}) (stroke (width 0.254) (type default)) (fill (type background))))'
 pinlines=[];instancepins=[]
 for j,pin in enumerate(pins):
  local_y=(n-1)*1.27-j*2.54;px=x-15.24;py=y-local_y;net=part['pins'][pin];net=aliases.get(net,net)
  pinlines.append(f'(pin passive line (at -15.24 {local_y} 0) (length 5.08) (name {q(pin)} {effects()}) (number {q(pin)} {effects()}))')
  instancepins.append(f'(pin {q(pin)} (uuid {uid(ref+"/"+pin)}))')
  if net and net!='NC':connections.append(f'(label {q(net)} (at {px} {py} 180) (effects (font (size 0.85 0.85)) (justify right bottom)) (uuid {uid(ref+"/label/"+pin)}))')
  else:connections.append(f'(no_connect (at {px} {py}) (uuid {uid(ref+"/nc/"+pin)}))')
 libs.append(f'(symbol "SCW:{ref}" (pin_names (offset 0)) (in_bom yes) (on_board yes) (property "Reference" "{ref[0]}" (at 0 0 0) {effects()}) (property "Value" "{ref}" (at 0 0 0) {effects()}) {body} (symbol "{ref}_1_1" {" ".join(pinlines)}))')
 mpn=bom[ref]['part_number']
 instances.append(f'(symbol (lib_id "SCW:{ref}") (at {x} {y} 0) (unit 1) (in_bom yes) (on_board yes) (dnp no) (uuid {uid(ref)}) (property "Reference" {q(ref)} (at {x} {y-half-3} 0) {effects()}) (property "Value" {q(mpn)} (at {x} {y+half+3} 0) {effects(.85)}) {" ".join(instancepins)} (instances (project "manual_rearm" (path "/{sheet}" (reference {q(ref)}) (unit 1)))))')
paper='A1' if len(asm['parts'])>49 else 'A2'
text=f'(kicad_sch (version 20230121) (generator eeschema) (uuid {sheet}) (paper "{paper}") (lib_symbols {" ".join(libs)}) (text "CONNECTION MIGRATION ONLY - generic passive pins; no footprints; not for fabrication" (at 297 15 0) {effects(1.5)} (uuid {uid("warning")})) {" ".join(connections)} {" ".join(instances)})\n'
(a.out/'manual_rearm.kicad_sch').write_text(text)
print(json.dumps({'components':len(instances),'pins':sum(len(p['pins']) for p in asm['parts']),'output':str(a.out)}))
