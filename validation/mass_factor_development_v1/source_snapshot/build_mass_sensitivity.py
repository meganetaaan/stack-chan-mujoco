#!/usr/bin/env python3
"""Build separate mass-only sensitivity plant; original collision geometry retained."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET
from compare_candidate_base_mass import aggregate

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--out', type=Path, required=True)
p.add_argument('--case', choices=['full','mass_only','com_only','inertia_only'], default='full', help='Diagnostic single-property changes are not manufacturable designs')
p.add_argument('--residual-grams', type=float, required=True, help='Assumed harness and unlisted hardware mass; not a qualified budget')
a = p.parse_args()
if a.out.exists() or not 0 <= a.residual_grams <= 100:
    p.error('New output and residual mass in [0,100] g required')
root = Path(__file__).resolve().parents[3]
ledger = root/'validation/candidate_base_mass_development_v1/report.json'
hardware = root/'validation/fastener_allowance_development_v1/report.json'
records = json.loads(ledger.read_text())['components']
old = records.pop('cables_and_fasteners')
if a.residual_grams:
    ratio = a.residual_grams/1000/old['mass_kg']
    records['unlisted_harness_hardware_assumption'] = dict(mass_kg=a.residual_grams/1000,
        com_base_m=old['com_base_m'], inertia_com_kg_m2=[[v*ratio for v in row] for row in old['inertia_com_kg_m2']])
for i, r in enumerate(json.loads(hardware.read_text())['rows']):
    records['listed_hardware_'+str(i)] = r
base = aggregate(records)
source = root/'software/sim/mujoco/assets/r9_fast_turn_v1'
full_base = base
if a.case != 'full':
    baseline = json.loads((source/'models/inertials.json').read_text())['base']
    key = {'mass_only':'mass_kg','com_only':'com_m','inertia_only':'inertia_kg_m2'}[a.case]
    base = dict(baseline)
    base[key] = full_base[key]
a.out.mkdir(parents=True)
shutil.copytree(source/'models',a.out/'models')
shutil.copytree(source/'reference',a.out/'reference')
shutil.copyfile(source/'robot.json',a.out/'robot.json')
path = a.out/'models/scene.xml'
tree = ET.parse(path)
node = tree.find('.//body[@name="base"]/inertial')
I = base['inertia_kg_m2']
node.attrib.clear()
node.set('mass',str(base['mass_kg']))
node.set('pos',' '.join(map(str,base['com_m'])))
node.set('fullinertia',' '.join(map(str,[I[0][0],I[1][1],I[2][2],I[0][1],I[0][2],I[1][2]])))
tree.write(path,encoding='unicode')
ipath = a.out/'models/inertials.json'
inertials = json.loads(ipath.read_text()); inertials['base'] = base
ipath.write_text(json.dumps(inertials,indent=2)+'\n')
plan = dict(scope=__doc__, case=a.case, full_candidate_base=full_base, residual_mass_grams=a.residual_grams, base=base,
            source_sha256={str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in (ledger,hardware)},
            criteria={'finite_simulation_required':True,'duration_s':7,'turn_error_limit_deg':1,'turn_target_abs_deg':90},
            limitations=['Original visual and collision geometry retained: not candidate interference acceptance.',
                         'Residual mass and its location are sensitivity assumptions, not a released harness design.',
                         'Hardware envelopes use assumed density and nominal geometry.',
                         'Only base inertia changed; original turn controller and motor parameters retained.'])
(a.out/'mass_plan.json').write_text(json.dumps(plan,indent=2)+'\n')
print(json.dumps(base))
