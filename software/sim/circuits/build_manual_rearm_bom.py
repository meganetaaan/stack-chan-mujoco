"""Resolve the current assembly and resistor overlay to a quantity BOM; no release implied."""
import argparse,csv,hashlib,json
from collections import defaultdict
from pathlib import Path
root=Path(__file__).resolve().parents[3]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
current=json.loads((root/'schematics/power/manual_rearm_current.json').read_text())
paths=[current['assembly'],current['resistor_selection']]
assembly,resistors=[json.loads((root/x).read_text()) for x in paths]
overlay={r['reference']:r for r in resistors['resistors']};groups=defaultdict(list)
for part in assembly['parts']:
 ref=part['reference']
 if ref.startswith('R'):
  selected=overlay[ref];key=(selected['part_number'],f"{selected['value_ohm']} ohm",'selected_candidate_not_released')
 elif ref.startswith('U'):key=(part['part'],'IC','selected_candidate_not_released')
 elif ref.startswith('C'):key=('UNSELECTED','100 nF nominal local bypass','part_rating_tolerance_effective_capacitance_pending')
 elif ref=='SW1':key=('UNSELECTED','Normally open momentary switch','B3U-1000P separate candidate not integrated')
 else:raise ValueError(ref)
 groups[key].append(ref)
assert set(overlay)=={p['reference'] for p in assembly['parts'] if p['reference'].startswith('R')}
rows=[{'part_number':k[0],'description':k[1],'quantity':len(refs),'references':' '.join(refs),'status':k[2]} for k,refs in groups.items()]
assert sum(r['quantity'] for r in rows)==assembly['part_count']==43
with (a.out/'bom.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=rows[0],lineterminator='\n');w.writeheader();w.writerows(rows)
report={'source_sha256':{x:hashlib.sha256((root/x).read_bytes()).hexdigest() for x in paths},'assembly_parts':assembly['part_count'],'bom_quantity':sum(r['quantity'] for r in rows),'selected_candidate_quantity':sum(r['quantity'] for r in rows if r['part_number']!='UNSELECTED'),'unselected_quantity':sum(r['quantity'] for r in rows if r['part_number']=='UNSELECTED'),'scope':'Manual rearm revH only; excludes main power path, brake, sequencer, raw button interface and independent stop','manufacturing_release':False,'electrical_qualification':False}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
