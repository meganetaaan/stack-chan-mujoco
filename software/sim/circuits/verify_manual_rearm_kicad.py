"""Check KiCad-exported connectivity against the current assembly and selected BOM."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parents[3]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--netlist', type=Path, required=True)
p.add_argument('--schematic', type=Path, required=True)
p.add_argument('--out', type=Path, required=True)
a = p.parse_args()
current_path = root / 'schematics/power/manual_rearm_current.json'
current = json.loads(current_path.read_text())
assembly_path = root / current['assembly']
bom_path = root / current['quantity_bom']
assembly = json.loads(assembly_path.read_text())
expected = {(part['reference'], pin): net for part in assembly['parts']
            for pin, net in part['pins'].items()}
values = {ref: row['part_number'] for row in csv.DictReader(bom_path.open())
          for ref in row['references'].split()}
xml = ET.parse(a.netlist).getroot()
actual_values = {c.attrib['ref']: c.findtext('value')
                 for c in xml.findall('./components/comp')}
assert actual_values == values, 'Selected component values differ'
seen = set()
connected = nc = 0
for net in xml.findall('./nets/net'):
    nodes = net.findall('node')
    for node in nodes:
        key = (node.attrib['ref'], node.attrib['pin'])
        assert key in expected and key not in seen, ('Unknown/duplicate pin', key)
        seen.add(key)
        wanted = expected[key]
        if not wanted or wanted == 'NC':
            assert len(nodes) == 1 and net.attrib['name'].startswith('unconnected-'), key
            assert 'no_connect' in node.attrib.get('pintype', ''), key
            nc += 1
        else:
            name = net.attrib['name']
            assert name.removeprefix('/') == wanted, (key, name, wanted)
            connected += 1
assert seen == set(expected), 'Missing pins'
paths = {'current': current_path, 'assembly': assembly_path, 'bom': bom_path,
         'schematic': a.schematic, 'readback': a.netlist}
report = {
    'kicad_exporter': xml.findtext('./design/tool'),
    'native_readback_connectivity_matches': True,
    'components': len(values), 'connected_pins': connected, 'declared_nc_pins': nc,
    'electrical_qualification': False,
    'limitations': ['Generic passive pin symbols; no electrical ERC qualification',
                   'No footprints; no board release',
                   'Sequencer and protection design remain incomplete'],
    'sha256': {name: hashlib.sha256(path.read_bytes()).hexdigest()
               for name, path in paths.items()}}
a.out.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
