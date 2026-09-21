"""Compose actual candidate pin maps; do not model IC behavior or certify safety."""
import argparse
import copy
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCES = {
    'BAT': 'schematics/power/battery_protection_integration_candidate_v1/assembly.json',
    'SYS': 'schematics/power/servo_power_pololu_discharge_candidate_v1/assembly.json',
}
# These are intentional system connections, not accidental equal-name merging.
BINDINGS = {'GND': 'PACK_RETURN', 'BATTERY_RAW': 'PACK_POS_PROTECTED',
            'DRIVE_BATTERY_PROTECTED': 'PACK_POS_PROTECTED'}


def compose():
    parts, traces, provenance = [], [], {}
    sources = {}
    for domain, relative in SOURCES.items():
        raw = (ROOT / relative).read_bytes()
        source = json.loads(raw)
        sources[domain] = source
        provenance[relative] = hashlib.sha256(raw).hexdigest()
        def net(name):
            if name is None:
                return None
            return name if domain == 'BAT' else BINDINGS.get(name, 'SYS__' + name)
        for original in source['parts']:
            part = copy.deepcopy(original)
            part['reference'] = domain + '__' + original['reference']
            part['pins'] = {pin: net(value) for pin, value in original['pins'].items()}
            # Nested source metadata retains source-local net names; use only pins
            # and interconnects for system connectivity.
            part['source_reference'] = original['reference']
            part['source_assembly'] = relative
            parts.append(part)
        for original in source.get('interconnects', []):
            trace = copy.deepcopy(original)
            trace.update(name=domain + '__' + original['name'],
                         **{'from': net(original['from']), 'to': net(original['to'])})
            traces.append(trace)
    inhibit_path = 'schematics/power/logic_predischarge_inhibit_candidate.json'
    raw = (ROOT / inhibit_path).read_bytes()
    inhibit = json.loads(raw)
    provenance[inhibit_path] = hashlib.sha256(raw).hexdigest()
    target = next(p for p in parts if p['reference'] == inhibit['target_reference'])
    assert target['pins'][inhibit['target_pin']] is None
    target['pins'][inhibit['target_pin']] = inhibit['net']
    for suffix, spec, ends in [
        ('PD', inhibit['pulldown'], [inhibit['net'], inhibit['reference_ground']]),
        ('SER', inhibit['series'], [inhibit['control_port'], inhibit['net']]),
    ]:
        parts.append({'reference': 'SYS__R_LOGIC_SHDN_' + suffix,
                      'part': spec['part'], 'value_ohm': spec['ohm'],
                      'pins': dict(zip(['1', '2'], ends)),
                      'source_reference': suffix, 'source_assembly': inhibit_path})
    iso_path = 'schematics/power/aux_start_isolator_candidate.json'
    raw = (ROOT / iso_path).read_bytes()
    iso = json.loads(raw)
    provenance[iso_path] = hashlib.sha256(raw).hexdigest()
    for original in iso['parts']:
        part = copy.deepcopy(original)
        part.update(source_reference=part['reference'], source_assembly=iso_path)
        parts.append(part)
    feed_path = 'schematics/power/stop_feed_candidate.json'
    raw = (ROOT / feed_path).read_bytes()
    feed = json.loads(raw)
    provenance[feed_path] = hashlib.sha256(raw).hexdigest()
    old_feed = next(p for p in parts if p['reference'] == feed['supersedes_reference'])
    assert old_feed['value_ohm'] == feed['old_nominal_ohm']
    assert list(old_feed['pins'].values()) == feed['nets']
    parts.remove(old_feed)
    for number in range(feed['quantity']):
        parts.append({'reference': 'SYS__R_STOP_INPUT_' + str(number),
                      'part': feed['part_each'], 'value_ohm': feed['resistance_each_ohm'],
                      'pins': dict(zip(['1','2'], feed['nets'])),
                      'source_reference': 'parallel_' + str(number), 'source_assembly': feed_path})
    refs = [part['reference'] for part in parts]
    assert len(refs) == len(set(refs))
    byref = {part['reference']: part for part in parts}
    # Union only explicit copper traces. Components, especially ICs, are NOT wires.
    parent = {}
    def find(value):
        parent.setdefault(value, value)
        if parent[value] != value:
            parent[value] = find(parent[value])
        return parent[value]
    for trace in traces:
        parent[find(trace['from'])] = find(trace['to'])
    checks = {
        'no_explicit_copper_short_across_shunt': find('CELL_B_MINUS') != find('PACK_RETURN'),
        'no_explicit_copper_short_across_main_fets': find('CELL_POS_FUSED') != find('PACK_POS_PROTECTED'),
        'no_explicit_copper_parallel_servo_outputs': find('SYS__LEFT_SERVO_BUS') != find('SYS__RIGHT_SERVO_BUS'),
        'logic_and_stop_input_on_protected_positive':
            byref['SYS__U_LOGIC_PROTECT']['pins']['8'] == 'PACK_POS_PROTECTED'
            and byref['SYS__R_STOP_INPUT_0']['pins']['1'] == 'PACK_POS_PROTECTED',
        'both_regulator_inputs_on_protected_positive': all(
            byref[f'SYS__{side}_U_REGULATOR']['pins']['VIN'] == 'PACK_POS_PROTECTED'
            for side in ('LEFT', 'RIGHT')),
        'bq_reference_separate_from_system_reference':
            byref['BAT__U_CELL_PROTECT']['pins']['17'] == 'CELL_B_MINUS'
            and byref['SYS__U_LOGIC_PROTECT']['pins']['17'] == 'PACK_RETURN',
    }
    assert all(checks.values()), checks
    unresolved = {p['reference']: p['unresolved_pins'] for p in parts if p.get('unresolved_pins')}
    missing_parts = [p['reference'] for p in parts if not p.get('part')]
    placeholder_parts = [p['reference'] for p in parts if any(
        marker in str(p.get('part', '')).lower()
        for marker in ('candidate', 'pending', 'unselected', 'unknown'))]
    suffix_pending = [p['reference'] for p in parts if p.get('ordering_suffix_pending')]

    required_design = [
        {'issue': 21, 'gap': 'Main battery connector, fuse/disconnect/reverse protection before CELL_POS_FUSED'},
        {'issue': 21, 'gap': 'Tab5 protected input branch and independent default-off inhibit; Tab5 is absent from this netlist'},
        {'issue': 21, 'gap': 'Local host supervisor/watchdog/latch connected; AUX crossing connected; analog qualification and rearm firmware incomplete'},
        {'issue': 24, 'gap': 'External PDSG switch/resistor, independent abort and TS2 wake/PCHG disposition'},
        {'issue': 22, 'gap': 'Predischarge budget includes automatic-start logic/stop branches, both disabled regulators, capacitors and Tab5 leakage'},
        {'issue': 23, 'gap': 'Complete startup/reset/brownout sequence with raw comparator outputs qualified before motor enable'},
        {'issue': 24, 'gap': 'Regulator ALLOW drivers and full qualification of BQ watchdog/latch inhibit path'},
        {'issue': 24, 'gap': 'Main/eFuse thresholds, inrush, regeneration, short-circuit energy, thermal and recovery qualification'},
    ]
    assembly = {
        'status': 'partial_system_connection_candidate', 'source_sha256': provenance,
        'bindings_SYS_to_BAT': BINDINGS,
        'system_overrides': ['SYS__U_LOGIC_PROTECT pin14: floating to SYS__LOGIC_SHDN; default-low network added', 'SYS__R_STOP_INPUT 1kohm replaced by2x1.5kohm parallel'],
        'connectivity_authority': 'parts[].pins and interconnects only; nested metadata is inherited source-local context',
        'parts': parts, 'interconnects': traces,
        'unimplemented_design': required_design,
        'electrically_operational': False, 'manufacturing_release': False,
    }
    report = {
        'source_sha256': provenance, 'parts': len(parts),
        'populated_pin_connections': sum(v is not None for p in parts for v in p['pins'].values()),
        'explicit_trace_count': len(traces), 'connection_checks': checks,
        'check_scope': 'Explicit net naming/copper only; no component conduction, leakage, transient, ground offset, layout or fault proof',
        'logic_inhibit_driver_present': True, 'logic_inhibit_driver_qualified': False,
        'unresolved_pins': unresolved, 'unselected_part_references': missing_parts,
        'placeholder_part_references': placeholder_parts,
        'ordering_suffix_pending_references': suffix_pending,
        'selection_audit_scope': 'Empty fields, descriptive placeholders and explicit suffix flags; other populated fields are not automatically qualified order codes',
        'tab5_branch_present': False, 'battery_host_present': 'BAT__U_BQ_HOST' in byref, 'system_sequencer_present': False,
        'predischarge_hardware_present': False,
        'unimplemented_design': required_design,
        'decision': 'HOLD: incomplete design, not eligible for manufacturing or Issue closure',
        'electrical_qualification': False, 'manufacturing_release': False,
    }
    return assembly, report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    assembly, report = compose()
    args.out.mkdir(parents=True, exist_ok=True)
    for name, value in [('assembly', assembly), ('report', report)]:
        (args.out / (name + '.json')).write_text(json.dumps(value, indent=2) + '\n')
    with (args.out / 'bom.csv').open('w', newline='') as stream:
        writer = csv.writer(stream, lineterminator='\n')
        writer.writerow(['reference', 'part', 'source_assembly', 'source_reference', 'selection_status'])
        for part in assembly['parts']:
            status = ('missing' if not part.get('part') else
                      'placeholder' if part['reference'] in report['placeholder_part_references'] else
                      'ordering_suffix_pending' if part.get('ordering_suffix_pending') else
                      'candidate_not_procurement_qualified')
            writer.writerow([part['reference'], part.get('part'), part['source_assembly'], part['source_reference'], status])
    with (args.out / 'connections.csv').open('w', newline='') as stream:
        writer = csv.writer(stream, lineterminator='\n')
        writer.writerow(['reference', 'pin', 'net'])
        for part in assembly['parts']:
            for pin, net in part['pins'].items():
                writer.writerow([part['reference'], pin, net])
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
