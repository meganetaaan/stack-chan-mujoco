"""Identify actual pin-map changes needed before removing raw-cell protection."""
import hashlib
import json
from collections import defaultdict
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT/'validation/protected_pack_transition_v1'
OUT.mkdir(exist_ok=True)
source = ROOT/'schematics/power/system_power_integration_candidate_v1/assembly.json'
a = json.loads(source.read_text())
remove = {p['reference'] for p in a['parts'] if p['reference'].startswith('BAT__')}
iso_refs = {'SYS__U_AUX_START_ISO','SYS__C_AUX_ISO_PRIMARY','SYS__C_AUX_ISO_SECONDARY'}
assert iso_refs <= {p['reference'] for p in a['parts']}
ends=defaultdict(list)
for p in a['parts']:
    for pin,net in p['pins'].items():
        if net is not None:
            ends[net].append({'reference':p['reference'],'pin':pin})
boundary=[]
for net,pins in ends.items():
    removed=[p for p in pins if p['reference'] in remove]
    kept=[p for p in pins if p['reference'] not in remove]
    if removed and kept:
        boundary.append({'net':net,'removed_pins':removed,'remaining_pins':kept})
assert {x['net'] for x in boundary} == {'CELL_B_MINUS','BQ_CTRL3V3','CELL_POS_FUSED','PACK_POS_PROTECTED','PACK_RETURN','BQ_AUX_START_REQUEST'}
remaining=[p for p in a['parts'] if p['reference'] not in remove|iso_refs]
ports={net:[e for e in ends[net] if e['reference'] not in remove|iso_refs]
       for net in ['SYS__LOGIC_START_ALLOW','PACK_POS_PROTECTED','PACK_RETURN','CELL_POS_FUSED','CELL_B_MINUS']}
assert ports['SYS__LOGIC_START_ALLOW'] == [{'reference':'SYS__R_LOGIC_SHDN_SER','pin':'1'}]
plan={'criteria':['Enumerate cross-boundary pins from current assembly, not document labels',
                  'Preserve power input, return and logic-enable replacements as explicit unresolved interfaces',
                  'No automatic connection from removed CELL nets to remaining PACK nets'],
      'stop':'One removal-impact enumeration; no new simulated PCM thresholds'}
(OUT/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
report={'source':str(source.relative_to(ROOT)), 'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'original_parts':len(a['parts']),'raw_cell_parts_removed':len(remove),
        'additional_isolator_parts_removed':sorted(iso_refs),'remaining_parts':len(remaining),
        'removed_references':sorted(remove|iso_refs),'raw_cell_boundary':boundary,
        'replacement_interface_pins':ports,
        'missing_functions':['Protected pack positive-to-distribution connection after inlet protection',
                             'Pack return connection; old current shunt is deleted',
                             'Logic start driver in PACK_RETURN domain',
                             'Independent fresh manual arm and reset/watchdog behavior formerly hosted in BAT domain',
                             'Pack undervoltage warning and Tab5 planned shutdown coordination',
                             'System input current measurement or justified replacement if needed by protection'],
        'notes':['Removing the isolator also removes its local decoupling; retain STOP supply capacitors',
                 'No assertion that PCM protects branch wiring or controls reverse/regeneration current',
                 'Part count reduction is not a mass, cost or safety equivalence claim'],
        'electrically_operational':False,'manufacturing_release':False}
(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ['raw_cell_boundary','removed_references','replacement_interface_pins']},indent=2))
