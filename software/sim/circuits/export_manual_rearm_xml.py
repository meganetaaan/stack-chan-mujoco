"""Export selected components and connectivity as KiCad-style intermediate XML, not a schematic."""
import argparse,csv,hashlib,json,xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict
root=Path(__file__).resolve().parents[3]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
current=json.loads((root/'schematics/power/manual_rearm_current.json').read_text());paths=[current['assembly'],current['quantity_bom'],current['quantity_bom_report']]
assembly=json.loads((root/paths[0]).read_text());bom=list(csv.DictReader((root/paths[1]).open()));br=json.loads((root/paths[2]).read_text())
for path,sha in br['source_sha256'].items():assert hashlib.sha256((root/path).read_bytes()).hexdigest()==sha,path
selected={}
for row in bom:
 refs=row['references'].split();assert len(refs)==int(row['quantity'])
 for ref in refs:
  assert ref not in selected;selected[ref]=row
assert set(selected)=={x['reference'] for x in assembly['parts']}
export=ET.Element('export',version='D');design=ET.SubElement(export,'design');ET.SubElement(design,'source').text=paths[0];ET.SubElement(design,'tool').text='stack-chan-walk intermediate connectivity exporter'
components=ET.SubElement(export,'components');nets=defaultdict(list);nc=[]
for part in assembly['parts']:
 ref=part['reference'];row=selected[ref];assert row['part_number']!='UNSELECTED'
 comp=ET.SubElement(components,'comp',ref=ref);ET.SubElement(comp,'value').text=row['part_number'];ET.SubElement(comp,'footprint').text=''
 fields=ET.SubElement(comp,'fields');ET.SubElement(fields,'field',name='SelectionStatus').text=row['status'];ET.SubElement(fields,'field',name='Description').text=row['description']
 for pin,net in part['pins'].items():
  if net is None or net=='NC':nc.append([ref,pin])
  else:nets[net].append((ref,pin))
node=ET.SubElement(export,'nets')
for code,(name,pins) in enumerate(sorted(nets.items()),1):
 net=ET.SubElement(node,'net',code=str(code),name=name)
 for ref,pin in pins:ET.SubElement(net,'node',ref=ref,pin=pin)
ET.indent(export);path=a.out/'manual_rearm.xml';ET.ElementTree(export).write(path,encoding='utf-8',xml_declaration=True)
# Read the actual artifact back and compare every component and connected pin.
loaded=ET.parse(path).getroot();actual={(n.attrib['ref'],n.attrib['pin'],net.attrib['name']) for net in loaded.findall('./nets/net') for n in net.findall('node')};expected={(part['reference'],pin,net) for part in assembly['parts'] for pin,net in part['pins'].items() if net and net!='NC'}
assert actual==expected
assert {c.attrib['ref']:c.findtext('value') for c in loaded.findall('./components/comp')}=={ref:row['part_number'] for ref,row in selected.items()}
report={'source_sha256':{x:hashlib.sha256((root/x).read_bytes()).hexdigest() for x in paths},'components':len(selected),'nets':len(nets),'connected_pins':len(actual),'unconnected_pins':nc,'roundtrip_graph_equal':True,'format':'KiCad-style intermediate XML version D; component and net sections','native_schematic':False,'KiCad_import_tested':False,'footprints_assigned':False,'manufacturing_release':False}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['components','nets','connected_pins','roundtrip_graph_equal','KiCad_import_tested']}))
