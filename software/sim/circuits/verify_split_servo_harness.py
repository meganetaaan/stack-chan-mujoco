"""Check exported harness pin assignments; this does not inspect physical wiring."""
import argparse
import copy
import csv
import hashlib
import json
from pathlib import Path


def check(rows, joints):
    errors = []
    definitions = {j['name']: j for j in joints}
    seen = set()
    connectors = {}
    for row in rows:
        name = row['joint']
        if name not in definitions:
            errors.append('unknown joint: ' + name)
            continue
        try:
            pin = int(row['pin'])
            bus_id = int(row['servo_id'])
        except ValueError:
            errors.append('invalid numeric field: ' + name)
            continue
        key = (name, pin)
        if key in seen:
            errors.append('duplicate terminal: ' + str(key))
        seen.add(key)
        if bus_id != definitions[name]['bus_id']:
            errors.append('servo ID mismatch: ' + name)
        connector = row['connector']
        if not connector or (connector in connectors and connectors[connector] != name):
            errors.append('connector shared by joints: ' + connector)
        connectors[connector] = name
        side = name.split('_')[0].upper()
        wanted = {1: 'POWER_RETURN_STAR', 2: side + '_SERVO_5V', 3: side + '_DATA'}
        if pin not in wanted or row['net'] != wanted[pin]:
            errors.append('wrong net: ' + str(key))
    required = {(name, pin) for name in definitions for pin in (1, 2, 3)}
    if seen != required:
        errors.append('terminal inventory mismatch')
    if len(connectors) != len(definitions):
        errors.append('connector inventory mismatch')
    return errors


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--csv', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    joint_path = Path('board/mechanical/prototype/joints.json')
    joints = json.loads(joint_path.read_text())
    rows = list(csv.DictReader(a.csv.open()))
    failures = check(rows, joints)
    mutations = {}
    changed = copy.deepcopy(rows); changed[1]['net'] = 'RIGHT_SERVO_5V'
    mutations['left_branch_on_right_rail'] = changed
    changed = copy.deepcopy(rows); changed[1]['net'], changed[2]['net'] = changed[2]['net'], changed[1]['net']
    mutations['power_data_swap'] = changed
    mutations['missing_return'] = rows[1:]
    mutations['duplicate_terminal'] = rows + [rows[0]]
    changed = copy.deepcopy(rows); changed[0]['servo_id'] = '999'
    mutations['wrong_servo_id'] = changed
    changed = copy.deepcopy(rows)
    for row in changed[3:6]: row['connector'] = rows[0]['connector']
    mutations['shared_connector_name'] = changed
    negative = {name: check(data, joints) for name, data in mutations.items()}
    report = {'connection_table_pass': not failures, 'errors': failures,
              'fault_injection_errors': negative,
              'all_injected_faults_detected': all(negative.values()),
              'source_hashes': {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                                for path in (a.csv, joint_path)},
              'physical_wiring_verified': False, 'electrical_qualification': False}
    a.out.mkdir(parents=True, exist_ok=False)
    (a.out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    if failures or not all(negative.values()):
        raise SystemExit('Harness verification failed; see report.json')
    print('36 terminals checked; six injected assignment faults rejected')


if __name__ == '__main__':
    main()
