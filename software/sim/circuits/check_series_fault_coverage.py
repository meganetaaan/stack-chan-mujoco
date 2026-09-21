"""Separate LT4363 fault comparison points from unproven operating bounds."""
import argparse
import hashlib
import json
from pathlib import Path

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--out', type=Path, required=True)
a = p.parse_args()
source = Path('validation/shunt_stability_comparison_v1/report.json')
data = json.loads(source.read_text())
row, = [r for r in data['rows'] if r['part'] == 'WSLF25124L000FEA' and r['quantity_per_leg'] == 2]
rmin = row['range_after_solder_and_TCR_ohm'][0]
# Use the actual tabulated VCC=12 V condition, not the 12.6 V battery maximum.
points = []
for name, out, sense in [('short_at_zero', 0., .035), ('foldback_at_one', 1., .035), ('full_limit_at_three', 3., .055)]:
    current = sense / rmin
    # OUT is after the shunt. Deduct shunt voltage for the MOSFET VDS.
    vds = 12. - out - sense
    points.append(dict(case=name, VCC_V=12., OUT_V=out, sense_limit_V=sense,
                       current_comparison_A=current, MOSFET_VDS_V=vds,
                       MOSFET_power_comparison_W=vds*current))
report = dict(
    source_sha256={str(source): hashlib.sha256(source.read_bytes()).hexdigest()},
    datasheet=dict(url='https://www.analog.com/media/en/technical-documentation/data-sheets/4363fb.pdf',
                   revision='C', section='Electrical Characteristics, page 4: current limit and foldback'),
    resistance_min_conditional_ohm=rmin,
    points=points,
    unqualified_ranges=[
        'OUT between 1 and 3 V: do not interpolate the typical foldback curve into a guaranteed maximum.',
        'VCC=5 V normal regulator operation and VCC=12.6 V regulator pass-through fault differ from the tabulated 12 V condition.',
        'Sensing bias, shared copper, drift and actual assembly process remain outside the resistor-only calculation.',
        'Current-limit timer differs from the overvoltage timer; series_clamp_timer_v3 is not the duration for these cases.',
        'Startup capacitance charging, gate transient, repetition and initial mounting-base temperature require a time-resolved SOA check.'
    ],
    decision='The OV comparison point does not bound all fault power. Do not qualify the FET or release the circuit from that point alone.',
    worst_case_fault_bound_verified=False, SOA_verified=False, manufacturing_release=False)
a.out.mkdir(parents=True, exist_ok=False)
(a.out/'report.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(points))
