"""Resolve the current assembly and resistor overlay to a quantity BOM; no release implied."""
import argparse,csv,hashlib,json
from collections import defaultdict
from pathlib import Path
root=Path(__file__).resolve().parents[3]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--assembly',help='Optional comparison assembly, repository-relative path');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
current=json.loads((root/'schematics/power/manual_rearm_current.json').read_text())
paths=[a.assembly or current['assembly'],current['resistor_selection']]
assembly,resistors=[json.loads((root/x).read_text()) for x in paths]
overlay={r['reference']:r for r in resistors['resistors']};groups=defaultdict(list)
caps=None
if current.get('capacitor_selection'):
 paths.append(current['capacitor_selection']);caps=json.loads((root/paths[-1]).read_text())
 assert set(caps['references'])=={p.get('origin_reference',p['reference']) for p in assembly['parts'] if p.get('origin_reference',p['reference']).startswith('C')}
 assert caps['nominal_capacitance_F']==1e-7

for part in assembly['parts']:
 ref=part['reference'];origin=part.get('origin_reference',ref)
 if origin.startswith('R') and origin in overlay:
  selected=overlay[origin];key=(selected['part_number'],f"{selected['value_ohm']} ohm",'selected_candidate_not_released')
 elif origin.startswith('R'):key=('UNSELECTED',part['part'],'exact_resistor_part_pending')
 elif origin.startswith('U'):key=(part['part'],'IC','selected_candidate_not_released')
 elif origin.startswith('C'):key=(caps['part_number'],'100 nF nominal local bypass',caps['status']) if caps else ('UNSELECTED','100 nF nominal local bypass','part_rating_tolerance_effective_capacitance_pending')
 elif ref=='SW1':key=(part['part'],'Local normally open momentary switch','selected_candidate_not_released') if part['part']=='B3U-1000P' else ('UNSELECTED','Normally open momentary switch','part_pending')
 else:raise ValueError(ref)
 groups[key].append(ref)
assert set(overlay)<={p.get('origin_reference',p['reference']) for p in assembly['parts'] if p.get('origin_reference',p['reference']).startswith('R')}
rows=[{'part_number':k[0],'description':k[1],'quantity':len(refs),'references':' '.join(refs),'status':k[2]} for k,refs in groups.items()]
assert sum(r['quantity'] for r in rows)==assembly['part_count']
with (a.out/'bom.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=rows[0],lineterminator='\n');w.writeheader();w.writerows(rows)
report={'source_sha256':{x:hashlib.sha256((root/x).read_bytes()).hexdigest() for x in paths},'assembly_parts':assembly['part_count'],'bom_quantity':sum(r['quantity'] for r in rows),'selected_candidate_quantity':sum(r['quantity'] for r in rows if r['part_number']!='UNSELECTED'),'unselected_quantity':sum(r['quantity'] for r in rows if r['part_number']=='UNSELECTED'),'scope':'Manual rearm assembly only; excludes main power path, brake, sequencer and independent stop','manufacturing_release':False,'electrical_qualification':False}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
